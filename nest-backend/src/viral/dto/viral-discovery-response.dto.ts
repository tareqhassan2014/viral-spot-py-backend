export class AnalysisDiscoveryDto {
  discovery_type: 'completed' | 'active';
  analysis_found: boolean;
  immediate_access: boolean;
  queue_id: string;
  session_id: string;
}

export class AnalysisDetailsDto {
  id: string;
  session_id: string;
  primary_username: string;
  status: string;
  progress_percentage: number;
  current_step: string;
  priority: number;
  total_runs: number;
}

export class TimelineInformationDto {
  submitted_at: string; // ISO time string (2025-08-06 19:00:02.641709+00)
  started_at?: string; // ISO time string
  completed_at?: string; // ISO time string
  analysis_age_hours?: number | null;
  freshness_status?: 'recent' | 'available';
  processing_duration_minutes?: number | null;
  estimated_completion?: string | null;
}

export class AccessInformationDto {
  results_endpoint: string;
  content_endpoint: string;
  status_endpoint: string;
  immediate_load: boolean;
}

export class SystemOptimizationDto {
  duplicate_prevention: boolean;
  resource_conservation: string;
  processing_saved: string;
  performance_benefit: string;
}

export class ErrorInformationDto {
  error_message?: string;
  has_errors: boolean;
}

export class MonitoringInformationDto {
  status_endpoint: string;
  polling_recommended: boolean;
  polling_interval_seconds: number;
  progress_available: boolean;
}

export class NextStepsDto {
  wait_for_completion: boolean;
  monitor_progress: string;
  expected_result_access: string;
  alternative_action: string;
}

export class RerunInformationDto {
  auto_rerun_enabled: boolean;
  can_trigger_rerun: boolean;
  rerun_recommendation: string;
}

export class ViralDiscoveryResponseDto {
  success: boolean;
  data: {
    analysis_discovery: AnalysisDiscoveryDto;
    analysis_details: AnalysisDetailsDto;
    timeline_information: TimelineInformationDto;
    access_information?: AccessInformationDto;
    system_optimization: SystemOptimizationDto;
    error_information: ErrorInformationDto;
    monitoring_information?: MonitoringInformationDto;
    next_steps?: NextStepsDto;
    rerun_information?: RerunInformationDto;
    analysis_type: 'completed' | 'active';
    timestamp: string;
  };
  message: string;
}
