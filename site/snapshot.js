const WORKFORCE_SNAPSHOT = {
 "org": {
  "metrics": {
   "manager_count": 15,
   "avg_span_of_control": 9.0,
   "overspan_managers": 5,
   "narrow_span_managers": 0,
   "max_org_depth": 2
  },
  "widest_spans": [
   {
    "employee_id": "EMP-0005",
    "department_code": "Customer Success",
    "band_code": "M2",
    "direct_reports": 15,
    "subtree_size": 15,
    "is_overspan": true
   },
   {
    "employee_id": "EMP-0004",
    "department_code": "Engineering",
    "band_code": "M2",
    "direct_reports": 12,
    "subtree_size": 12,
    "is_overspan": true
   },
   {
    "employee_id": "EMP-0007",
    "department_code": "Sales",
    "band_code": "M2",
    "direct_reports": 12,
    "subtree_size": 12,
    "is_overspan": true
   },
   {
    "employee_id": "EMP-0015",
    "department_code": "Sales",
    "band_code": "M2",
    "direct_reports": 12,
    "subtree_size": 12,
    "is_overspan": true
   },
   {
    "employee_id": "EMP-0003",
    "department_code": "Sales",
    "band_code": "M1",
    "direct_reports": 11,
    "subtree_size": 11,
    "is_overspan": true
   },
   {
    "employee_id": "EMP-0002",
    "department_code": "Engineering",
    "band_code": "M1",
    "direct_reports": 10,
    "subtree_size": 10,
    "is_overspan": false
   },
   {
    "employee_id": "EMP-0001",
    "department_code": "People Ops",
    "band_code": "M2",
    "direct_reports": 9,
    "subtree_size": 9,
    "is_overspan": false
   },
   {
    "employee_id": "EMP-0006",
    "department_code": "Customer Success",
    "band_code": "M1",
    "direct_reports": 8,
    "subtree_size": 8,
    "is_overspan": false
   }
  ]
 },
 "pay_equity": {
  "metrics": {
   "fte_headcount": 109,
   "unadjusted_gap_pct": -0.168482229428,
   "adjusted_gap_pct": -0.028094807292
  },
  "cohorts": [
   {
    "department_code": "Customer Success",
    "band_code": "M1",
    "gender_cohort": "Men",
    "cohort_size": 5,
    "is_suppressed": false,
    "avg_comp_ratio_safe": 1.0766
   },
   {
    "department_code": "Customer Success",
    "band_code": "M2",
    "gender_cohort": "Men",
    "cohort_size": 7,
    "is_suppressed": false,
    "avg_comp_ratio_safe": 0.9062
   },
   {
    "department_code": "Engineering",
    "band_code": "M1",
    "gender_cohort": "Men",
    "cohort_size": 5,
    "is_suppressed": false,
    "avg_comp_ratio_safe": 0.8961
   },
   {
    "department_code": "Finance",
    "band_code": "IC3",
    "gender_cohort": "Men",
    "cohort_size": 5,
    "is_suppressed": false,
    "avg_comp_ratio_safe": 0.9727
   },
   {
    "department_code": "Sales",
    "band_code": "IC3",
    "gender_cohort": "Women",
    "cohort_size": 6,
    "is_suppressed": false,
    "avg_comp_ratio_safe": 1.006
   },
   {
    "department_code": "Customer Success",
    "band_code": "IC3",
    "gender_cohort": "Men",
    "cohort_size": 3,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Customer Success",
    "band_code": "IC4",
    "gender_cohort": "Men",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Customer Success",
    "band_code": "IC4",
    "gender_cohort": "Women",
    "cohort_size": 2,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Customer Success",
    "band_code": "IC5",
    "gender_cohort": "Men",
    "cohort_size": 4,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Customer Success",
    "band_code": "IC5",
    "gender_cohort": "Women",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Customer Success",
    "band_code": "M1",
    "gender_cohort": "Women",
    "cohort_size": 2,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Customer Success",
    "band_code": "M2",
    "gender_cohort": "Women",
    "cohort_size": 2,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Engineering",
    "band_code": "IC3",
    "gender_cohort": "Women",
    "cohort_size": 4,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Engineering",
    "band_code": "IC4",
    "gender_cohort": "Men",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Engineering",
    "band_code": "IC4",
    "gender_cohort": "Women",
    "cohort_size": 2,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Engineering",
    "band_code": "IC5",
    "gender_cohort": "Men",
    "cohort_size": 2,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Engineering",
    "band_code": "IC5",
    "gender_cohort": "Women",
    "cohort_size": 2,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Engineering",
    "band_code": "M1",
    "gender_cohort": "Non-binary",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Engineering",
    "band_code": "M1",
    "gender_cohort": "Women",
    "cohort_size": 2,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Engineering",
    "band_code": "M2",
    "gender_cohort": "Men",
    "cohort_size": 3,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Engineering",
    "band_code": "M2",
    "gender_cohort": "Women",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Finance",
    "band_code": "IC3",
    "gender_cohort": "Women",
    "cohort_size": 3,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Finance",
    "band_code": "IC4",
    "gender_cohort": "Men",
    "cohort_size": 2,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Finance",
    "band_code": "IC4",
    "gender_cohort": "Women",
    "cohort_size": 4,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Finance",
    "band_code": "M1",
    "gender_cohort": "Men",
    "cohort_size": 3,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Finance",
    "band_code": "M1",
    "gender_cohort": "Non-binary",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Finance",
    "band_code": "M1",
    "gender_cohort": "Women",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Finance",
    "band_code": "M2",
    "gender_cohort": "Men",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Finance",
    "band_code": "M2",
    "gender_cohort": "Women",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "People Ops",
    "band_code": "IC4",
    "gender_cohort": "Men",
    "cohort_size": 4,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "People Ops",
    "band_code": "IC4",
    "gender_cohort": "Women",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "People Ops",
    "band_code": "IC5",
    "gender_cohort": "Men",
    "cohort_size": 4,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "People Ops",
    "band_code": "IC5",
    "gender_cohort": "Women",
    "cohort_size": 2,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "People Ops",
    "band_code": "M1",
    "gender_cohort": "Men",
    "cohort_size": 3,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "People Ops",
    "band_code": "M2",
    "gender_cohort": "Men",
    "cohort_size": 2,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "People Ops",
    "band_code": "M2",
    "gender_cohort": "Women",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Sales",
    "band_code": "IC3",
    "gender_cohort": "Men",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Sales",
    "band_code": "IC4",
    "gender_cohort": "Women",
    "cohort_size": 3,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Sales",
    "band_code": "IC5",
    "gender_cohort": "Men",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Sales",
    "band_code": "IC5",
    "gender_cohort": "Women",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Sales",
    "band_code": "M1",
    "gender_cohort": "Men",
    "cohort_size": 4,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Sales",
    "band_code": "M1",
    "gender_cohort": "Women",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Sales",
    "band_code": "M2",
    "gender_cohort": "Men",
    "cohort_size": 3,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   },
   {
    "department_code": "Sales",
    "band_code": "M2",
    "gender_cohort": "Women",
    "cohort_size": 1,
    "is_suppressed": true,
    "avg_comp_ratio_safe": null
   }
  ]
 },
 "voice": {
  "metrics": {
   "transcript_count": 18,
   "exit_transcript_count": 13,
   "stay_transcript_count": 5,
   "negative_transcript_count": 9,
   "multi_reason_transcript_count": 13,
   "flight_risk_signal_count": 7,
   "avg_sentiment": -0.15635850555555555
  },
  "reasons_primary": [
   {
    "reason": "career_growth",
    "n": 6
   },
   {
    "reason": "manager",
    "n": 3
   },
   {
    "reason": "compensation",
    "n": 2
   },
   {
    "reason": "work_life_balance",
    "n": 2
   },
   {
    "reason": "workload_burnout",
    "n": 2
   },
   {
    "reason": "compensation_equity",
    "n": 1
   },
   {
    "reason": "org_change",
    "n": 1
   },
   {
    "reason": "positive_no_issue",
    "n": 1
   }
  ],
  "reasons_any": [
   {
    "reason": "career_growth",
    "n": 9
   },
   {
    "reason": "manager",
    "n": 5
   },
   {
    "reason": "workload_burnout",
    "n": 4
   },
   {
    "reason": "compensation",
    "n": 3
   },
   {
    "reason": "compensation_equity",
    "n": 3
   },
   {
    "reason": "work_life_balance",
    "n": 3
   },
   {
    "reason": "org_change",
    "n": 2
   },
   {
    "reason": "positive_no_issue",
    "n": 2
   }
  ],
  "corroborated": [
   {
    "employee_id": "EMP-0031",
    "interview_type": "exit",
    "sentiment_score": -0.5332031,
    "primary_reason": "compensation_equity",
    "secondary_reason": "manager",
    "comp_ratio": 0.7961,
    "rating_score": 4,
    "transcript_text": "I found out in a meeting, by accident, that a colleague who joined after me on the same band is earning materially more. We do identical work. I did not raise it because I did not want to be that person, but then I did not raise it for eight months either, which is worse. I have asked for a correction twice and been told the offer was 'market at the time'. The gap is not the problem. The silence is.",
    "review_text": "Top performer on the platform migration; noted pay feels out of step with market and is interviewing externally."
   },
   {
    "employee_id": "EMP-0005",
    "interview_type": "exit",
    "sentiment_score": -0.42578125,
    "primary_reason": "career_growth",
    "secondary_reason": null,
    "comp_ratio": 0.7995,
    "rating_score": 4,
    "transcript_text": "I was passed over for the senior role in March. I was told it was 'not quite the right timing' and that I should keep demonstrating leadership, which I have done -- I have since led two cross-team projects end to end. I am not asking for a title to sit on, I want the scope. If that is not coming, I would rather go somewhere it is.",
    "review_text": "Consistently high-quality output; no retention concerns raised."
   },
   {
    "employee_id": "EMP-0003",
    "interview_type": "exit",
    "sentiment_score": -0.3125,
    "primary_reason": "compensation",
    "secondary_reason": "workload_burnout",
    "comp_ratio": 0.765,
    "rating_score": 4,
    "transcript_text": "I have accepted a role elsewhere. To be straight with you, the money was the deciding factor and it was not close. I was offered roughly thirty percent more base, and I did the maths on what I was actually being paid per hour once on-call was factored in. I like the team, genuinely, but I have watched three people leave for the same reason in a year and nothing changed.",
    "review_text": "Exceeded goals again this cycle; in our 1:1 raised a competing offer and asked about band placement."
   },
   {
    "employee_id": "EMP-0008",
    "interview_type": "exit",
    "sentiment_score": -0.30078125,
    "primary_reason": "career_growth",
    "secondary_reason": "manager",
    "comp_ratio": 0.8077,
    "rating_score": 4,
    "transcript_text": "The work is not the problem, the framing is. We have decided I am a manager, but I do not want to manage people -- I want to keep going deeper on the technical track. We do not have a dual track, so staying means becoming something I do not want to be. I have been unwilling to say this out loud until now, which is its own problem.",
    "review_text": "Top performer on the platform migration; noted pay feels out of step with market and is interviewing externally."
   },
   {
    "employee_id": "EMP-0007",
    "interview_type": "exit",
    "sentiment_score": -0.1328125,
    "primary_reason": "manager",
    "secondary_reason": "career_growth",
    "comp_ratio": 0.7686,
    "rating_score": 4,
    "transcript_text": "My manager left in January and nobody was appointed for four months. In that time I had no one to go to -- I was escalating things into the void and getting no response. When the new manager arrived she inherited a backlog and prioritised other people's. I feel like I have been invisible since January. I have started interviewing.",
    "review_text": "Exceeded goals for the second straight quarter; strong peer feedback on mentorship."
   }
  ]
 },
 "band": {
  "metrics": {
   "total_headcount": 150,
   "red_circle_count": 0,
   "below_range_count": 37,
   "in_floor_cluster_count": 4,
   "below_range_rate": 0.246667
  },
  "by_band": [
   {
    "band_code": "IC3",
    "headcount": 30,
    "below_range_count": 10,
    "red_circle_count": 0,
    "in_floor_cluster_count": 2,
    "avg_range_penetration": 0.236231333333,
    "compression_ratio": 0.170732
   },
   {
    "band_code": "IC4",
    "headcount": 28,
    "below_range_count": 8,
    "red_circle_count": 0,
    "in_floor_cluster_count": 0,
    "avg_range_penetration": 0.260882857143,
    "compression_ratio": 0.170732
   },
   {
    "band_code": "IC5",
    "headcount": 22,
    "below_range_count": 4,
    "red_circle_count": 0,
    "in_floor_cluster_count": 1,
    "avg_range_penetration": 0.343155545455,
    "compression_ratio": 0.170732
   },
   {
    "band_code": "M1",
    "headcount": 38,
    "below_range_count": 7,
    "red_circle_count": 0,
    "in_floor_cluster_count": 0,
    "avg_range_penetration": 0.382215289474,
    "compression_ratio": 0.170732
   },
   {
    "band_code": "M2",
    "headcount": 32,
    "below_range_count": 8,
    "red_circle_count": 0,
    "in_floor_cluster_count": 1,
    "avg_range_penetration": 0.337475375,
    "compression_ratio": 0.170732
   }
  ],
  "overlap": [
   {
    "lower_band": "M1",
    "upper_band": "IC5",
    "overlap_index": 0.714286
   },
   {
    "lower_band": "IC5",
    "upper_band": "M2",
    "overlap_index": 0.360902
   },
   {
    "lower_band": "IC4",
    "upper_band": "M1",
    "overlap_index": 0.252747
   },
   {
    "lower_band": "IC3",
    "upper_band": "IC4",
    "overlap_index": 0.0
   }
  ]
 },
 "governance": {
  "tests": [
   {
    "test_id": 1,
    "metric_name": "governed_headcount",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 2,
    "metric_name": "naive_headcount",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 3,
    "metric_name": "avg_span_of_control",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 4,
    "metric_name": "overspan_managers",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 5,
    "metric_name": "manager_count",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 6,
    "metric_name": "women_avg_comp_ratio",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 7,
    "metric_name": "men_avg_comp_ratio",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 8,
    "metric_name": "voice_transcript_count",
    "status": "PASS",
    "model_dependent": true
   },
   {
    "test_id": 9,
    "metric_name": "voice_exit_transcript_count",
    "status": "PASS",
    "model_dependent": true
   },
   {
    "test_id": 10,
    "metric_name": "voice_stay_transcript_count",
    "status": "PASS",
    "model_dependent": true
   },
   {
    "test_id": 11,
    "metric_name": "voice_sentiment_out_of_range",
    "status": "PASS",
    "model_dependent": true
   },
   {
    "test_id": 12,
    "metric_name": "voice_unclassified_rows",
    "status": "PASS",
    "model_dependent": true
   },
   {
    "test_id": 13,
    "metric_name": "voice_negative_transcript_count",
    "status": "PASS",
    "model_dependent": true
   },
   {
    "test_id": 14,
    "metric_name": "voice_multi_reason_transcript_count",
    "status": "PASS",
    "model_dependent": true
   },
   {
    "test_id": 15,
    "metric_name": "voice_flight_risk_signal_count",
    "status": "PASS",
    "model_dependent": true
   },
   {
    "test_id": 16,
    "metric_name": "voice_corroborated_flight_risk_count",
    "status": "PASS",
    "model_dependent": true
   },
   {
    "test_id": 17,
    "metric_name": "voice_career_growth_primary_count",
    "status": "PASS",
    "model_dependent": true
   },
   {
    "test_id": 18,
    "metric_name": "band_total_headcount",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 19,
    "metric_name": "band_red_circle_count",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 20,
    "metric_name": "band_below_range_count",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 21,
    "metric_name": "band_below_range_rate",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 22,
    "metric_name": "band_in_floor_cluster_count",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 23,
    "metric_name": "band_wtd_avg_range_penetration",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 24,
    "metric_name": "band_m1_ic5_overlap_index",
    "status": "PASS",
    "model_dependent": false
   },
   {
    "test_id": 25,
    "metric_name": "band_findings_total",
    "status": "PASS",
    "model_dependent": false
   }
  ],
  "registry_size": {
   "n": 29,
   "unowned": 0
  },
  "alerts": [
   {
    "alert_type": "BAND_ARCHITECTURE",
    "severity": "HIGH",
    "detail": "Band review flagged 41 employees: 37 below range minimum, 0 red circle, 4 clustered at the floor. REPORTS ONLY - no pay values are proposed or changed by this procedure.",
    "created_at": "2026-09-25T10:47:18.010000"
   },
   {
    "alert_type": "PAY_EQUITY_DRIFT",
    "severity": "HIGH",
    "detail": "Adjusted gap -2.81% exceeds the 2% threshold - escalate to Compensation Committee. Unadjusted -16.85%.",
    "created_at": "2026-09-22T01:12:46.542000"
   },
   {
    "alert_type": "PAY_EQUITY_DRIFT",
    "severity": "HIGH",
    "detail": "Adjusted gap -2.8100000000000001% exceeds the 2% threshold - escalate to Compensation Committee. Unadjusted -16.850000000000001%.",
    "created_at": "2026-09-21T09:21:13.787000"
   }
  ],
  "tasks": [
   {
    "name": "BAND_ARCHITECTURE_QUARTERLY",
    "schedule": "USING CRON 0 4 1 1,4,7,10 * UTC",
    "state": "started"
   },
   {
    "name": "METRIC_REGRESSION_DAILY",
    "schedule": "USING CRON 30 2 * * * UTC",
    "state": "started"
   },
   {
    "name": "PAY_EQUITY_DRIFT_WEEKLY",
    "schedule": "USING CRON 0 3 * * 1 UTC",
    "state": "started"
   }
  ]
 },
 "exported_at": "26-Sep-2026"
};
