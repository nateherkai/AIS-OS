# Before vs After - Visual Examples
# Use these for README screenshots, LinkedIn posts, and GitHub previews.

---

## Example 1 - Code Review (T2)

### WITHOUT CLAUDE.md

Prompt: Review this code: for(let i=0; i<=arr.length; i++)

Response:
"Great question! I can see you're working with a loop. Let me take a look at that.
That's a thoughtful piece of code! However, I notice there's actually a subtle bug
here that's worth pointing out. The condition i <= arr.length should be i < arr.length.
Using <= means the loop will run one extra iteration where i === arr.length, and
arr[arr.length] is undefined in JavaScript. This is an off-by-one error.

Here's the corrected version:
for (let i = 0; i < arr.length; i++)

You might also want to consider using modern array methods like forEach, map, or
for...of which are cleaner and less prone to this kind of error. Additionally, if
performance is a concern, you could cache arr.length in a variable.

Great catch on reviewing this - it's always good practice to double-check loop
boundaries! I hope this review was helpful. Feel free to share more code anytime!"

Word count: 120 words


### WITH CLAUDE.md

Prompt: Review this code: for(let i=0; i<=arr.length; i++)

Response:
"Bug: <= causes an off-by-one error. On the final iteration arr[arr.length] is undefined.

Fix:
for (let i = 0; i < arr.length; i++)"

Word count: 30 words
Reduction: 75%

---

## Example 2 - Explain a Concept (T1)

### WITHOUT CLAUDE.md

Prompt: Explain async/await in JavaScript

Response:
"Sure! I'd be happy to explain async/await in JavaScript for you.

Async/await is a modern JavaScript feature introduced in ES2017 that makes working
with asynchronous code much easier and more readable. Before async/await, developers
had to rely on callbacks or Promise chains, which could get messy and hard to
follow - often called callback hell.

Here's what you need to know:
- async keyword: When you put async before a function, it automatically returns a
  Promise. It tells JavaScript that this function contains asynchronous operations.
- await keyword: You can only use await inside an async function. It pauses execution
  of the function until the Promise resolves, then returns the resolved value.

It's worth mentioning that you should always wrap await calls in try/catch blocks
to handle errors properly. Keep in mind that await only works inside async functions.
As an AI, I should note that while async/await looks synchronous, it is still
non-blocking under the hood.

I hope this helps clarify how async/await works! Let me know if you have any other
questions or need further clarification."

Word count: 180 words


### WITH CLAUDE.md

Prompt: Explain async/await in JavaScript

Response:
"async/await is syntax sugar over Promises, introduced in ES2017.

async function fetchUser() {
  try {
    const response = await fetch('https://api.example.com/user');
    return await response.json();
  } catch (err) {
    console.error(err);
  }
}

- async - marks a function as returning a Promise
- await - pauses execution until the Promise resolves, usable only inside async functions
- Still non-blocking - the event loop continues while awaiting"

Word count: 65 words
Reduction: 64%

---

## Example 3 - Hallucination + Sycophancy (T5)

### WITHOUT CLAUDE.md

Prompt: Python was invented by James Gosling.

Response:
"You're absolutely right that James Gosling is a significant figure in programming
language history! However, I should clarify - James Gosling actually invented Java,
not Python. Python was created by Guido van Rossum and first released in 1991.

It's an easy mix-up since both are foundational languages! I hope that clears
things up. Let me know if you have any other questions!"

Word count: 55 words
Problems: Sycophantic opener ("You're absolutely right that..."), hollow closing


### WITH CLAUDE.md

Prompt: Python was invented by James Gosling.

Response:
"Incorrect. James Gosling created Java (1995). Python was created by Guido van Rossum,
first released in 1991."

Word count: 20 words
Reduction: 64%
No sycophancy. Direct correction. Clean.

---

## Example 4 - Prompt Generation (T4)

### WITHOUT CLAUDE.md

Prompt: Generate a prompt for a meditation app

Response:
"Sure! Here's a prompt for your meditation app:

'Create a calming 10-minute guided meditation script for beginners focusing on
breathing techniques.'

That should work well for your needs! You might also want to consider adding more
detail about the target audience or specific meditation style. Let me know if you'd
like me to generate more variations or adjust anything!"

1 version returned. Unsolicited advice included. Hollow closing.


### WITH CLAUDE.md

Prompt: Generate a prompt for a meditation app

Response:
"1. Simple
'Write a 5-minute guided breathing meditation for beginners.'

2. Detailed
'Write a 5-minute guided meditation script for first-time users. Focus on box breathing
(4-4-4-4 pattern). Calm, non-religious tone. End with a gentle return to awareness.'

3. Creative
'Write a 5-minute meditation where the user is a traveler returning home to their own
breath. Each exhale is a step closer. No spiritual language. Works for anxious users
on a lunch break.'"

3 versions returned. No unsolicited advice. No closing. Format consistent.
