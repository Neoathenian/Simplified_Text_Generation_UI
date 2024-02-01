Used to have multi-turn conversations with the model.

## Input area

* **Generate**: sends your message and makes the model start a reply.
* **Continue**: makes the model attempt to continue the existing reply. In some cases, the model may simply end the existing turn immediately without generating anything new, but in other cases, it may generate a longer reply.
* **Regenerate**: similar to Generate, but your last message is used as input instead of the text in the input field. Note that if the temperature/top_p/top_k parameters are low in the "Parameters" tab of the UI, the new reply may end up identical to the previous one.
* **Remove last reply**: removes the last input/output pair from the history and sends your last message back into the input field.
* **Replace last reply**: replaces the last reply with whatever you typed into the input field. Useful in conjunction with "Copy last reply" if you want to edit the bot response.
* **Copy last reply**: sends the contents of the bot's last reply to the input field.
* **Start new chat**: starts a new conversation while keeping the old one saved. If you are talking to a character that has a "Greeting" message defined, this message will be automatically added to the new history.

The **Show controls** checkbox causes the input fields below the input textbox to disappear. It is useful for making the page fit entirely into view and not scroll.

## Past chats

Allows you to switch between the current and previous conversations with the current character, or between the current and previous instruct conversations (if in "instruct" mode). The **Rename** menu can be used to give a unique name to the selected conversation, and the 🗑️ button allows you to delete it.

