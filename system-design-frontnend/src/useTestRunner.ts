import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from './api';
import { type LoadTestConfig, type TestResult } from './types';

export function useTestRunner() {
  const [testId, setTestId] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const startTestMutation = useMutation({
    mutationFn: (config: LoadTestConfig) => api.startTest(config),
    onSuccess: (response) => {
      setTestId(response.test_id);
      if (response.status === 'running' || response.status === 'pending') {
        setAutoRefresh(true);
      }
    },
  });

  const {
    data: testResult,
    isLoading: isLoadingResult,
    error: resultError,
    refetch: refetchResult,
  } = useQuery({
    queryKey: ['testResult', testId],
    queryFn: () => api.getTestResult(testId!),
    enabled: !!testId,
    refetchInterval: autoRefresh ? 2000 : false,
    refetchOnWindowFocus: false,
  });

  const {
    data: testStatus,
    isLoading: isLoadingStatus,
  } = useQuery({
    queryKey: ['testStatus', testId],
    queryFn: () => api.getTestStatus(testId!),
    enabled: !!testId && autoRefresh,
    refetchInterval: autoRefresh ? 1000 : false,
    refetchOnWindowFocus: false,
  });

  // Stop auto-refresh when test is completed
  if (testResult?.status === 'completed' || testResult?.status === 'failed') {
    if (autoRefresh) {
      setAutoRefresh(false);
    }
  }

  const startTest = (config: LoadTestConfig) => {
    startTestMutation.mutate(config);
  };

  const fetchResults = () => {
    if (testId) {
      refetchResult();
    }
  };

  const toggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh);
  };

  const resetTest = () => {
    setTestId(null);
    setAutoRefresh(false);
  };

  return {
    testId,
    testResult,
    testStatus,
    isStarting: startTestMutation.isPending,
    isLoadingResult,
    isLoadingStatus,
    startError: startTestMutation.error,
    resultError,
    autoRefresh,
    startTest,
    fetchResults,
    toggleAutoRefresh,
    resetTest,
  };
}