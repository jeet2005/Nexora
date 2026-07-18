# Nexora Community Feedback and Research Contribution System

## Overview

The Nexora community system extends the platform with structured feedback, research contribution tracking, contributor reputation, administrator review workflows, and recognition features. It is designed for students, researchers, early testers, and platform administrators who need a professional way to submit ideas, track progress, reward useful reports, and surface high-value contributors.

This system does not replace or redesign the existing Nexora interface. It extends the current product with additional pages, profile sections, backend endpoints, and administrator controls that follow the existing white, mint-accented, minimal Nexora design language.

## Goals

- Encourage users to submit bugs, feature requests, dataset requests, research feedback, UI notes, and performance observations.
- Give users visibility into feedback status, administrator replies, stars, badges, and implementation progress.
- Provide administrators with a structured review workflow for triage, replies, prioritization, pinning, duplicate marking, status changes, and contributor recognition.
- Create a reputation system that rewards useful platform contributions with contribution points, badges, levels, and administrator stars.
- Add public-facing contribution signals to profiles and community leaderboards.

## User-Facing Features

### Submit Feedback

Route: `/feedback/new`

Users can submit structured feedback with the following fields:

- Title
- Category
- Description
- Priority
- Suggestion
- Screenshot or file attachment metadata

Supported categories:

- Bug
- Feature Request
- Dataset
- Research
- UI
- Performance
- Other

Supported priorities:

- Low
- Normal
- High
- Urgent

### My Feedback

Route: `/feedback`

Users can review every feedback item they have submitted. Each feedback card includes:

- Title
- Category
- Submission date
- Current status
- Administrator reply count
- Administrator stars
- Badge awarded, when applicable
- Recent administrator replies

Supported statuses:

- Waiting
- Under Review
- Planned
- Implemented
- Closed
- Duplicate

### Community Leaderboard

Route: `/community`

The leaderboard ranks contributors by contribution score and displays:

- Rank
- Contributor name
- Progression level
- Contribution score
- Administrator stars
- Badge count
- Feedback count

Supported period controls are included for weekly, monthly, and all-time views. The current backend implementation returns all-time rankings while keeping the API shape ready for period-specific filtering.

### Profile Reputation

The authenticated user profile now includes a community reputation section below the existing profile information. It displays:

- Contribution score
- Progression level
- Feedback accepted
- Features suggested
- Bugs reported
- Replies received
- Badges earned
- Administrator stars
- Earned badges with hover reasons

### Public Profile Contributions

Public profiles now include contribution information when reputation data exists:

- Contribution score
- Progression level
- Administrator stars
- Implemented suggestions
- Badges
- Recent feedback with status

### Community Notifications

The notifications page now includes community notifications for:

- Administrator replies
- Feedback stars
- Badge awards
- Implemented suggestions

## Administrator Features

### Feedback Review Console

Route: `/admin/feedback`

Administrators can review and manage submitted feedback from a dedicated admin page. Available actions include:

- Reply to feedback
- Assign administrator stars from 0 to 3
- Pin feedback
- Assign priority
- Change status
- Mark feedback as duplicate
- Award badges
- Mark suggestions as planned, implemented, closed, or under review

### Admin Star System

Administrators can award up to three stars to a feedback item:

| Stars | Meaning |
| :--- | :--- |
| 1 | Helpful Feedback |
| 2 | Excellent Suggestion |
| 3 | Outstanding Contribution |

Stars increase contributor reputation and appear in profile, feedback, and leaderboard contexts.

### Admin Analytics

The admin feedback console includes summary analytics:

- Feedback submitted
- Open feedback
- Implemented feedback
- Closed feedback
- Most requested categories
- Top contributors

## Reputation and Gamification

The contribution score is calculated from user activity across the feedback system. It currently rewards:

- Submitted feedback
- Accepted feedback
- Implemented suggestions
- Administrator replies received
- Administrator stars
- Badges earned

Progression levels:

| Level | Name |
| :--- | :--- |
| Level 1 | Explorer |
| Level 2 | Contributor |
| Level 3 | Researcher |
| Level 4 | Innovator |
| Level 5 | Pioneer |

## Badge System

Supported badges include:

- Founding Tester
- Early Adopter
- Community Supporter
- Research Contributor
- Feedback Champion
- Top Tester
- Bug Hunter
- Dataset Explorer
- Verified Researcher
- Power User

Badges include descriptive reasons and can be surfaced on profile pages, public profiles, feedback items, and leaderboard contexts.

## Backend API Summary

User community routes are mounted under `/api/community`.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| POST | `/api/community/feedback` | Submit feedback |
| GET | `/api/community/feedback/me` | List current user's feedback |
| POST | `/api/community/feedback/{feedback_id}/reactions` | Add a reaction |
| GET | `/api/community/profile/{user_id}/reputation` | Get reputation summary |
| GET | `/api/community/leaderboard` | Get contributor leaderboard |
| GET | `/api/community/notifications` | Get community notifications |

Administrator routes are mounted under `/api/admin/feedback`.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| GET | `/api/admin/feedback` | List all feedback |
| GET | `/api/admin/feedback/analytics` | Get admin feedback analytics |
| PATCH | `/api/admin/feedback/{feedback_id}` | Update status, priority, stars, pinning, duplicate, or badge |
| POST | `/api/admin/feedback/{feedback_id}/replies` | Reply to feedback |

## Persistence

The backend follows Nexora's existing persistence pattern:

- MongoDB is used when the configured persistence backend is available.
- Local JSON file storage is used as a fallback for local development and smoke tests.

Community feedback is stored in `community_feedback`.
Community notifications are stored in `notifications`.

## Implementation Notes

The implementation is intentionally modular:

- Backend router: `backend/app/routers/community.py`
- Frontend API client: `frontend/src/api/community.ts`
- User pages:
  - `frontend/src/pages/SubmitFeedbackPage.tsx`
  - `frontend/src/pages/MyFeedbackPage.tsx`
  - `frontend/src/pages/CommunityLeaderboardPage.tsx`
- Admin page:
  - `frontend/src/admin/pages/FeedbackReview.tsx`
- Extended existing pages:
  - `frontend/src/pages/Profile.tsx`
  - `frontend/src/pages/PublicProfilePage.tsx`
  - `frontend/src/pages/NotificationsPage.tsx`

## Design Constraints

The community system follows the existing Nexora UI direction:

- No redesign of existing pages
- No removed features
- White background
- Mint accent color
- Minimal layout
- Soft shadows and rounded cards consistent with the current app
- Compact, operational UI copy
- Reusable API and page components

## Future Enhancements

Recommended next iterations:

- Persist uploaded screenshot and file binaries instead of metadata only.
- Add full reaction displays and reaction analytics.
- Add follower and following relationships.
- Add contribution heatmap data and visualizations.
- Add period-specific leaderboard filtering for weekly and monthly views.
- Add notification read/unread state controls.
- Add admin assignment and internal notes.
- Add public feedback browsing and search.
- Add richer profile showcase controls for pinned achievements, best dataset, best feedback, and favorite model.
