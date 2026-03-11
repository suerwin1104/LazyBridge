SELECT task_id,
    task_type,
    status,
    error_msg
FROM task_trace
ORDER BY created_at DESC
LIMIT 5;