# Coaching context

Private AI profiles build context from canonical Mongo records and original
account-scoped messages. Self-host AI stays opt-in. This adds no independent
memory store, browser snapshot, or model-written facts.

The coach receives the current coffee and recipe, recent measured brews, bounded
cross-coffee references, and earlier bags or batches belonging to the same bean.
Earlier results carry their coffee/bag/storage provenance. They are comparisons,
not proof that a different portion will taste the same.

Conversation history covers the same bean across bags and batches, including
archived ones: at most 24 messages and 32,000 characters, in chronological order.
Up to 12 original owner reports are quoted separately with source IDs. The
current request remains explicit. User-reported taste and drink preference are
evidence even when the shot's corresponding fields are blank; they do not become
invented measurements or silently overwrite shot records.

The current batch's owner-marked reference or locked recipe takes priority.
Otherwise the highest recorded enjoyment rating precedes a generic good/balanced
outcome. The anchor explains its selection reason. Technical outcome, balance,
and enjoyment stay separate.

An explicit owner step declaration is retrieved from recent account-scoped
correction messages and quoted in equipment context. Decimal formatting and
assistant replies do not establish a grinder increment. Without a declaration,
the candidate generator omits numeric grind adjustments. This is the owner's
practical increment, not a universal mechanical detent. Older declarations
remain sourced observations and may need clarification after equipment changes.

Coaching guidance requires evidence and uncertainty: slow does not necessarily
mean bitter, sour does not necessarily require finer grinding, and roast/process
or frozen storage does not prove a particular cause. The model should describe
one experiment and its tradeoff, honor intended drink/enjoyment, and acknowledge
a changed recommendation when new evidence warrants one. All existing action,
revision, account and planned-versus-logged validation remains authoritative.

Replay methodology and commands are in [COACH_BENCHMARK.md](../scripts/COACH_BENCHMARK.md).
Private fixtures, transcripts and assessments remain in ignored `data/`.
