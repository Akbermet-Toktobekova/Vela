// Focused component regressions without a browser or additional dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const ts = require('../apps/mobile/node_modules/typescript');
const React = require('../apps/mobile/node_modules/react');
const root = path.resolve(__dirname, '..');
const baselineIndex = process.argv.indexOf('--baseline');
const baseline = baselineIndex >= 0 ? process.argv[baselineIndex + 1] : null;
if (baselineIndex >= 0 && !baseline) throw new Error('Supply a git revision after --baseline');
function load(file, mocks) {
  const source = baseline ? execFileSync('git', ['show', `${baseline}:${file}`], {cwd:root, encoding:'utf8'}) : fs.readFileSync(path.join(root,file),'utf8');
  const code = ts.transpileModule(source,{compilerOptions:{jsx:ts.JsxEmit.React,module:ts.ModuleKind.CommonJS,esModuleInterop:true,target:ts.ScriptTarget.ES2022}}).outputText;
  const module={exports:{}};
  vm.runInNewContext(code,{exports:module.exports,module,require:name=>{
    if (name in mocks) return mocks[name];
    throw new Error(`Unexpected import ${name}`);
  }, Date,Intl,URL,AbortController,setTimeout,clearTimeout});
  return module.exports;
}
const api=load('apps/mobile/src/lib/api.ts',{'react-native':{Platform:{OS:'web'}},'expo-secure-store':{}});
function harness(file, state) {
  let slots=[], cursor=0, tree=[];
  const commands=[]; const calls=[]; const routes=[];
  const connection={ready:true,connected:true};
  const query={isPending:false,isError:false,data:state};
  function slot(init) {const i=cursor++; if (!(i in slots)) slots[i]=init(); return [slots[i],v=>{slots[i]=v;}];}
  function mutation() {
    const [m]=slot(()=>({isPending:false,isSuccess:false,error:null,data:undefined,variables:undefined,
      reset(){this.error=null;this.data=undefined;this.variables=undefined;this.isSuccess=false;},
      mutate(value){this.variables=value;calls.push(value);}}));
    return m;
  }
  const stateMock={useCommand:()=>{const m=mutation(); if(!commands.includes(m))commands.push(m); return m;},useConnection:()=>connection,useFinancialState:()=>query};
  const ui=Object.fromEntries(['Button','Card','Chip','Copy','Field','Notice','Row','Screen','Loading'].map(x=>[x,x]));
  const mocks={react:{...React,useState:init=>slot(()=>typeof init==='function'?init():init)},'react-native':{View:'View'},'expo-router':{router:{push:r=>routes.push(r),replace:r=>routes.push(r)},Redirect:'Redirect'},'@tanstack/react-query':{useMutation:mutation,useQuery:()=>({})}};
  for(const prefix of ['../','../../']){
    mocks[prefix+'components/ui']=ui;
    mocks[prefix+'components/StateGate']={StateGate:({children})=>children(state)};
    mocks[prefix+'components/GoalCard']={GoalCard:'GoalCard'};
    mocks[prefix+'lib/state']=stateMock;
    mocks[prefix+'lib/api']=api;
    mocks[prefix+'theme']={space:{},usePalette:()=>({})};
  }
  mocks['./ui']=ui;
  const component=load(file,mocks);
  const render=()=>{cursor=0;tree=[];const walk=n=>{if(n==null||typeof n==='boolean')return;if(Array.isArray(n)){n.forEach(walk);return;}if(typeof n!=='object'){tree.push(n);return;}if(typeof n.type==='function'){walk(n.type(n.props));return;}tree.push(n);walk(n.props?.children);};walk(component.default?React.createElement(component.default):React.createElement(component.StateGate,{children:()=>null}));};
  const find=(type,label)=>tree.find(n=>n?.type===type&&n.props.label===label)?.props;
  render();
  return {render,find,commands,calls,routes,connection,query,tree:()=>tree,text:()=>tree.filter(x=>typeof x==='string').join(' '),setPreview:data=>{const m=slots.find(x=>x&&typeof x.mutate==='function'&&!commands.includes(x));Object.assign(m,data);}};
}
function fixture(){return {revision:3,available:-2000,actions:[{id:'a1',status:'planned',amount:4000,can_complete:false,created_on:'2026-10-28'}],snapshot:{cash:100000,saved:0,goal_target:100000,horizon:api.localDate(30),obligations:[]},summary:{transaction_count:0},recommendation:{amount:2000,kind:'save'},breakdown:{cash:100000,saved:0,protected:10000,bills:80000,planned:0},debts:[]};}
const tests={
 'shortfall allows cancel but no completion'(){const h=harness('apps/mobile/src/app/(tabs)/plan.tsx',fixture());assert.ok(h.find('Button','Cancel step'));assert.equal(h.find('Button','Mark done'),undefined);h.find('Button','Cancel step').onPress();assert.equal(h.calls[0].path,'/v1/actions/a1/cancel');},
 'bill errors clear on edits and close; impossible dates never submit'(){const h=harness('apps/mobile/src/app/(tabs)/plan.tsx',fixture());h.find('Button','+ Add bill').onPress();h.render();h.find('Field','Bill name').onChangeText('Extra');h.render();h.find('Field','Amount (EUR)').onChangeText('80');h.render();const due=`Due (≤ ${fixture().snapshot.horizon})`;h.find('Field',due).onChangeText('2026-02-30');h.render();h.find('Button','Save bill').onPress();h.render();assert.match(h.text(),/valid calendar date/);assert.equal(h.calls.length,0);h.find('Field',due).onChangeText(api.localDate(1));h.render();assert.doesNotMatch(h.text(),/valid calendar date/);h.commands[1].error=new Error('Server rejected bill');h.render();assert.match(h.text(),/Server rejected bill/);h.find('Field','Bill name').onChangeText('Extra revised');h.render();assert.doesNotMatch(h.text(),/Server rejected bill/);h.find('Button','Save bill').onPress();assert.equal(h.calls[0].body.obligation.amount,8000);h.commands[1].error=new Error('Server rejected bill');h.find('Button','Close').onPress();h.render();assert.doesNotMatch(h.text(),/Server rejected bill/);},
 'preview must match input and revision before save'(){const s=fixture();s.available=10000;const h=harness('apps/mobile/src/app/adjust.tsx',s);assert.ok(h.find('Button','Add to my plan').disabled);h.find('Field','Amount in EUR').onChangeText('40');h.render();h.setPreview({isSuccess:true,variables:'40',data:{revision:3,amount:4000,eligible:true}});h.render();assert.equal(h.find('Button','Add to my plan').disabled,false);h.commands[0].error=new Error('Old error');h.find('Field','Amount in EUR').onChangeText('150');h.render();assert.ok(h.find('Button','Add to my plan').disabled);assert.doesNotMatch(h.text(),/Old error/);h.setPreview({isSuccess:true,variables:'40',data:{revision:3,amount:4000,eligible:true}});h.render();assert.ok(h.find('Button','Add to my plan').disabled);h.find('Button','Add to my plan').onPress();assert.equal(h.calls.length,0);h.setPreview({isSuccess:true,variables:'150',data:{revision:2,amount:15000,eligible:true}});h.render();assert.ok(h.find('Button','Add to my plan').disabled);},
 'disconnected deep route redirects rather than loading forever'(){const h=harness('apps/mobile/src/components/StateGate.tsx',fixture());h.connection.connected=false;h.query.isPending=true;h.render();assert.ok(h.tree().some(n=>n?.type==='Redirect'&&n.props.href==='/connect'));h.connection.ready=false;h.render();assert.ok(h.tree().some(n=>n?.type==='Loading'));},
 'Today exposes client-side Learn navigation'(){const h=harness('apps/mobile/src/app/(tabs)/index.tsx',fixture());h.find('Button','Learn about money').onPress();assert.equal(h.routes[0],'/learn');},
 'internal validation diagnostics are hidden, useful errors preserved'(){assert.equal(api.apiErrorMessage('1 validation error for Snapshot input_value=secret','Check fields'),'Check fields');assert.equal(api.apiErrorMessage([{msg:'invalid'}],'Check fields'),'Check fields');assert.equal(api.apiErrorMessage('Refresh your data and try again.','Check fields'),'Refresh your data and try again.');}
};
let failed=0;for(const [name,test] of Object.entries(tests)){try{test();console.log('PASS',name);}catch(e){failed++;console.error('FAIL',name, e.message);}}
console.log(`${Object.keys(tests).length-failed}/${Object.keys(tests).length} PASS`);process.exitCode=failed?1:0;
