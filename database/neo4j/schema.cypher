CREATE INDEX cipher_project_name IF NOT EXISTS
FOR (n:Project)
ON (n.name);

CREATE INDEX cipher_task_status IF NOT EXISTS
FOR (n:Task)
ON (n.status);

CREATE INDEX cipher_task_deadline IF NOT EXISTS
FOR (n:Task)
ON (n.deadline);

CREATE INDEX cipher_task_title IF NOT EXISTS
FOR (n:Task)
ON (n.title);

CREATE INDEX cipher_reminder_trigger_time IF NOT EXISTS
FOR (n:Reminder)
ON (n.trigger_time);

CREATE INDEX cipher_reminder_status IF NOT EXISTS
FOR (n:Reminder)
ON (n.status);

CREATE INDEX cipher_reminder_last_triggered_at IF NOT EXISTS
FOR (n:Reminder)
ON (n.last_triggered_at);

CREATE INDEX cipher_event_start_time IF NOT EXISTS
FOR (n:Event)
ON (n.start_time);

CREATE INDEX cipher_event_end_time IF NOT EXISTS
FOR (n:Event)
ON (n.end_time);

CREATE INDEX cipher_event_title IF NOT EXISTS
FOR (n:Event)
ON (n.title);

CREATE INDEX cipher_note_title IF NOT EXISTS
FOR (n:Note)
ON (n.title);

CREATE INDEX cipher_person_name IF NOT EXISTS
FOR (n:Person)
ON (n.name);
