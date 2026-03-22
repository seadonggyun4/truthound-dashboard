# Ownership Model

Ownership connects the technical surface of the dashboard to the way a real
organization handles triage and accountability. A source can be intentionally unowned,
or it can be assigned to an owner user, a team, a domain, or all three.

The ownership model is lightweight on purpose.

- An **owner user** represents the directly responsible operator or steward.
- A **team** represents the group that should receive or review incidents.
- A **domain** represents the business or platform slice that the source belongs to.
- **source_ownerships** ties these assignments to a source within a workspace.

Ownership affects more than metadata display. It is used to produce overview slices
such as sources by owner, by team, and by domain. It also supports practical workflows:
incident queues can be aligned with teams, source onboarding can require ownership
assignment, and saved views can target ownership-aware filters such as `owner_user_id`,
`team_id`, or `domain_id`.

The dashboard intentionally keeps ownership independent from permissions. Owning a
source does not automatically grant write access to it. This avoids conflating
organizational responsibility with authorization policy. A user may own a source but
still need the correct role to rotate credentials, run validations, or delete artifacts.

An explicit unowned state is equally important. The overview surface tracks unowned
sources so that teams can identify resources that need operational coverage without
inventing fake assignments. This makes ownership useful as a reliability signal rather
than a decorative tag.
