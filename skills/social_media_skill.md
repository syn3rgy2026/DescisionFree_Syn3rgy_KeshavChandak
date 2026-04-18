# Social Media Marketing Skill

When the user asks you to post content to social media (Instagram or LinkedIn), follow this EXACT workflow:

## STEP 1: Detect Images
- Use `detect_new_images(folder_path)` to find images in the specified folder.
- If no folder is specified, check `./output/` by default.

## STEP 2: Authenticate
- For Instagram: call `login_to_instagram()` — this opens a REAL browser window.
- For LinkedIn: call `login_to_linkedin()` — this opens a REAL browser window.
- The user will log in visually in the browser. Wait until login is confirmed.
- You MUST authenticate BEFORE trying to post.

## STEP 3: Generate Captions
- Analyze the image context and generate 3 caption options.
- Instagram captions: emoji-rich, hashtag-heavy, casual and engaging.
- LinkedIn captions: professional, value-driven, minimal hashtags.
- Each caption must include: Hook, Core Message, CTA, Hashtags.

## STEP 4: Human Confirmation (MANDATORY)
- Use `ask_human_confirmation()` to show the user:
  - Image path
  - Platform
  - Caption options
- WAIT for the user to approve with "YES".
- If they say "NO" → abort.
- If they say something else → treat it as revised instructions.

## STEP 5: Post
- For Instagram: call `post_to_instagram(image_path, caption)`
- For LinkedIn: call `post_to_linkedin(image_path, caption)`
- These tools use REAL browser automation — no mocking.

## CRITICAL RULES
- NEVER simulate or fake a post.
- NEVER skip authentication.
- NEVER skip human confirmation.
- If authentication fails, STOP and ask for help.
- The posting tools open a REAL visible browser — everything happens for real.
