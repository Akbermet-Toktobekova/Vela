"""One bounded leased import operation; scheduling is an explicit worker process."""
import asyncio
from datetime import date
import json
from .ai import AIUnavailable
from .imports import build_preview, ImportError_
from .storage import StorageUnavailable


class ImportWorker:
    def __init__(self,repository,quotas,*,parser=build_preview,today=date.today):
        self.repository,self.quotas,self.parser,self.today=repository,quotas,parser,today

    async def run_once(self):
        job=self.repository.claim()
        if job is None:return False
        payload=json.loads(job['payload'])
        async def heartbeat():
            while True:
                await asyncio.sleep(self.repository.config.heartbeat_seconds)
                if not self.repository.heartbeat(job):return
        task=asyncio.create_task(heartbeat())
        try:
            data=self.repository.storage.read_file(job['owner'],job['file_id'])
            preview=await self.parser(data,payload['filename'],payload['content_type'],self.quotas,self.today(),
                'job-'+job['job_id'],external_ai_allowed=payload['processing']['external_ai'])
            self.repository.finish(job,preview)
        except asyncio.CancelledError:
            # Leave the lease durable; a replacement worker can reclaim expiry.
            raise
        except ImportError_ as error:
            self.repository.fail(job,permanent=not isinstance(error.__cause__,AIUnavailable),
                                 code='processing_unavailable' if isinstance(error.__cause__,AIUnavailable) else 'unsupported_or_invalid_source')
        except (FileNotFoundError,ValueError):
            self.repository.fail(job,permanent=True,code='unsupported_or_invalid_source')
        except (StorageUnavailable,AIUnavailable):
            self.repository.fail(job,code='processing_unavailable')
        except Exception:
            # Never persist provider/internal diagnostics or raw source details.
            self.repository.fail(job,code='processing_unavailable')
        finally:
            task.cancel()
            try:await task
            except asyncio.CancelledError:pass
        return True
