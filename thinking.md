# PART 3 — THINKING QUESTIONS

## Question A — Immediate Response

“Hi, I’m very sorry about the inconvenience, especially this late at night. I’ve alerted the on-call support and maintenance team immediately so they can investigate the hot water issue as a priority. We understand the urgency with your guests arriving in the morning, and someone from our team will contact you shortly with an update.”

I chose this wording because the first priority at 3am is to calm the guest and show that action is already being taken. This response acknowledges the frustration without sounding defensive and avoids making refund promises that the AI should not decide automatically.

---

## Question B — System Design

Beyond replying to messages, as soon as the message arrives, the system should classify it as a high priority operational complaint because it affects guest experience and upcoming hospitality operations. An urgent incident ticket should be created automatically.

The system should notify the on call operations manager, maintenance staff, and backup escalation contact through SMS, WhatsApp, push notification, or automated calls. The ticket should include booking details, timestamps, villa information, previous complaint history, and the full conversation thread.

The platform should also log important metadata like complaint category, AI confidence score, escalation reason, response timestamps, and whether human intervention was required.

If no human acknowledges the issue within 30 minutes, the system should automatically escalate the case to a secondary manager and trigger repeated alerts every few minutes until someone responds. Internally, the reservation should also be marked as a critical operational issue so future staff immediately see its priority level.

This creates accountability and reduces the risk of late night complaints being ignored.


---

## Question C — The Learning

A third hot water complaint in two months shows this is no longer an isolated incident. It is a recurring operational failure.

The system should automatically detect repeated complaint patterns by property and issue type. Villa B1 should immediately receive a maintenance risk flag and require preventive inspection before the next guest check in.

I would build a lightweight issue trend and risk scoring system. It would track complaint frequency, maintenance history, resolution time, and guest sentiment across all properties.

If the same issue crosses a threshold, the platform should automatically create preventive maintenance workflows instead of waiting for another guest complaint. In this case, the system could schedule boiler inspection, plumbing checks, or equipment replacement before the problem happens again.

The goal is not only to respond faster but to reduce repeat operational failures completely.