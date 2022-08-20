# Task Analytics

Differences to Celery Analytics:

- One table for both succeeded and failed tasks makes queries easier
- Retried tasks are missing completely from celery analytics
- Purpose of this app is to be useful within AA and not require additional tools like Grafana to work
- Adding more information about tasks, e.g. which are also available in flower

Objectives:

- App should not requires any additional tools to work
- Provide helpful information for admins to trouble shoot issues
- Should be useful for both beginner admins and experts
- Should not add any significant extra load on a system with default settings
- Should provide the ability to export the data to other tools (e.g. via CSV)
