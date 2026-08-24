import { useState, useEffect } from 'react';
import { jobsApi, JobStatusResponse } from '@/services/api';

export function useJobPoller(jobId: string | null, pollIntervalMs = 2000) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }

    let isSubscribed = true;
    let timerId: NodeJS.Timeout | null = null;

    const poll = async () => {
      try {
        setLoading(true);
        const data = await jobsApi.getJobStatus(jobId);
        if (isSubscribed) {
          setJob(data);
          setError(null);

          // Continue polling if job is still in progress
          if (data.status === 'QUEUED' || data.status === 'PROCESSING') {
            timerId = setTimeout(poll, pollIntervalMs);
          }
        }
      } catch (err: any) {
        if (isSubscribed) {
          setError(err.message || 'Failed to poll job status.');
        }
      } finally {
        if (isSubscribed) {
          setLoading(false);
        }
      }
    };

    poll();

    return () => {
      isSubscribed = false;
      if (timerId) clearTimeout(timerId);
    };
  }, [jobId, pollIntervalMs]);

  return { job, loading, error };
}
