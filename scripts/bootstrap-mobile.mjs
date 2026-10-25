// SDK-specific modules are resolved by Expo's own bundled compatibility map.
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const cwd = fileURLToPath(new URL('../apps/mobile/', import.meta.url));
function run(command, args) {
  const result = spawnSync(command, args, { cwd, stdio: 'inherit', shell: process.platform === 'win32' });
  if (result.status !== 0) process.exit(result.status ?? 1);
}
run('npm', ['install', '--no-audit', '--no-fund']);
run('npx', ['expo', 'install', 'expo-router', 'expo-secure-store', 'expo-font', 'expo-status-bar', 'expo-linking',
  'expo-constants', 'expo-dev-client', 'react-native-safe-area-context', 'react-native-screens',
  'react-native-web', 'react-dom', '@expo/vector-icons']);
run('npm', ['install', '@tanstack/react-query@^5', '@expo-google-fonts/manrope@^0.4']);
run('npx', ['expo', 'install', 'typescript', '@types/react', '--dev']);
run('npx', ['expo', 'install', '--fix']);
run('npm', ['run', 'typecheck']);
run('npx', ['expo-doctor']);
