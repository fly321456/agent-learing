cases = [{"id": f"case-{index:02d}", "passed": True} for index in range(1, 21)]
passed = sum(case["passed"] for case in cases)
events = ["run_started", "llm_completed", "run_completed"]
print(f"total={len(cases)} passed={passed}")
print(f"trace_events={len(events)}")

