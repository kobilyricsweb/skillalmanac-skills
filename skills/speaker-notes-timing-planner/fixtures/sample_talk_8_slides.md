# Why our quarterly release review runs long

Good morning everyone, and thank you for joining this quarterly review. Today I will walk through what happened to the release schedule over the last three months, why it slipped, and what we plan to change before the next cycle starts. Every claim in this deck ties to a number you can check on the dashboard afterwards. Please hold questions until the end of each section, because several answers depend on details that appear later in the deck. We have a lot to cover, so I will keep a steady pace and leave time for discussion at the end. If you have to leave early, here is the one sentence that summarizes the whole review: we shipped fewer releases than planned, the delay came mostly from review queues rather than engineering, and the fix is a smaller set of checkpoints with named owners. Everything else in this deck supports that sentence. Let me also be clear about scope. This review covers the four product teams that ship to customers every two weeks, the shared platform team that supports them, and the two external vendors whose work sits on the critical path for three of our largest launches this year. It does not cover the research group, which reports separately. The format is the same as last quarter. Each team lead gives a short readout, I pull the cross-team numbers together, and we finish with decisions. The appendix holds the raw export and the query that produced each figure, so anyone can rerun it after the meeting. Finally, a note on tone. Several delays this quarter were painful for the people involved, and some were the result of decisions I made. I will say so directly when that is the case. The purpose of this review is to improve how we work, not to assign blame to individuals. Let us begin with the numbers.

---

## What we planned and what we shipped

At the start of the quarter we committed to twenty-six releases across four product teams. We shipped nineteen on the promised date, four shipped more than a week late, and three were still open when the review window closed. That is a hit rate of about seventy-three percent, below the target we set in January. The gap is not evenly spread. The platform team delivered every committed item. The billing team delivered four of five, and the search team delivered five of seven, with both misses waiting on the same external review. The growth team had the largest gap, because one feature changed scope twice after the initial estimate. A late release is not automatically a failure, since several holds were deliberate quality decisions. The real question is whether each slip was predictable, visible early, and handled with a clear decision. Compared with the same period last year, the total number of releases is higher, which is the part people tend to remember. The average time from code complete to customer availability, however, rose by roughly four days. More releases with longer waiting times usually means more work sitting in queues. Most slips were visible at least a week before the due date, yet in many cases nobody made a call until the due date had already passed. Of the seven items that slipped by more than a week, five had a visible risk flag at least ten days before the due date. That gives us a concrete target for the next cycle: every risk flag should trigger a named decision within two working days, and the decision should be visible on the same board.

---

## Where the time actually went

We measured elapsed time in each stage: development, code review, quality assurance, legal and content review, and final approval. Development and code review look normal. The unexpected number is legal and content review, which absorbed about thirty-eight percent of elapsed time for late items. Review is a queue, not a bottleneck in itself. Items enter when the owning team marks them ready, and reviewers pick them up in fixed batches. An item that misses one batch waits for the next, which can add five working days. Handoffs between teams added further delay, because most cross-team requests had no standard format and needed a meeting before anyone could estimate. Rework also reset the review clock, since a change after review forced a full restart instead of a recheck of the changed section. The chart for this has one bar per stage and a second bar for queue time inside each stage. Queue time is the number to watch, because it responds to scheduling decisions rather than engineering effort. Development estimates were mostly accurate; the wrong estimates assumed that a review would take as long as the work itself and that a handoff would be a single message.

---

## Causes ranked by impact

If we could fix only three causes, the ranking would be this. First, review queue timing, which accounts for about half of the excess delay on late items. Second, incomplete handoff requests, which account for roughly a quarter. Third, rework that resets the review clock. Engineering estimation errors are real, but they are the smallest category this quarter. Queue timing is the largest cause because it is the least visible. At least six items this quarter were ready before a batch cutoff, yet the owners did not know the batch existed. The ranking changes if you weight by revenue, which moves two billing items higher, but this deck uses count-weighted ranking throughout. The count-weighted ranking matches what the team leads observed in their own tracker reviews, so it is the basis for every decision in this deck.

---

## Proposed plan for the next cycle

The plan has four parts, each with a named owner and a date. The first is a fixed review window: legal and content review runs on Tuesdays and Thursdays, with a noon cutoff for each batch. Items marked ready after the cutoff move to the next window. The second is a standard handoff request for every cross-team dependency, and the tracker will block the due-date field until the template is complete. The third is revision tracking, so a reviewer rechecks only the changed section. The goal is to cut the average rework cycle from six working days to two. The fourth is a decision deadline: every risk flag triggers a named decision within two working days, reviewed every Monday, with escalation to the team lead by Wednesday. We are not changing the release calendar, team structure, or vendor contracts this cycle.

---

## Decisions for today

I am asking the steering group for three decisions today. First, approve the fixed review window and the noon cutoff, starting the first Tuesday after the next planning cycle. Second, make the handoff template mandatory for cross-team items, with the tracker block in place by the end of the month. Third, approve the two-day decision deadline for risk flags. Each decision has a cost. The review window constrains ready dates, the template adds a few minutes per request, and leads must make calls they would previously have deferred. I believe each cost is smaller than the delay we absorbed this quarter, but the group should weigh that for itself. Owners will confirm their dates in writing by the end of the week. Please raise any objection now.

---

## Risks and open questions

The review window depends on reviewers keeping their slots. Two reviewers are covering a second queue this quarter, and if that continues the fixed window will slip the same way the old schedule did. I will track reviewer capacity weekly and raise it here if it becomes a constraint. Vendor delays affected two launches, but they were covered in last month's vendor review and are not repeated here. The revenue-weighted ranking is in the appendix for anyone who wants to compare it with the count-weighted version used in this deck. The vendor review action items are listed in the appendix under external dependencies, with owners and dates.

---

## Closing summary and next steps

To close, we shipped about seventy-three percent of planned releases on the promised date. The biggest source of delay was the timing of legal and content review, not engineering. The fix is a fixed review window, a standard handoff request, a faster revision cycle, and a decision deadline for every risk flag. Each change has a named owner and a date. The decision summary, the appendix, and the raw export will go to the steering group within one working day. I will repeat the sentence from the start, because it is what I want to be true at the next review: we are shipping more, we are waiting less, and every risk has an owner who decides within two working days. Thank you all for your candor today. We will take questions now, then move on to the team readouts.
