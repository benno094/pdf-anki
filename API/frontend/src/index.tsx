import { Streamlit, RenderData } from "streamlit-component-lib"

// Adds note to a deck
async function addFlashcard(deck: string, front: string, back: string, tags: string) {
  try {
    const note = {
      deckName: deck,
      modelName: 'Basic',
      fields: { Front: front, Back: back },
      options: { allowDuplicate: false },
      tags: [tags],
    };
    const addNoteResponse = await fetch('http://localhost:8765', {
      method: 'POST',
      body: JSON.stringify({
        action: 'addNote',
        params: { note: note },
        version: 6,
      }),
    });

    await addNoteResponse.json();
  } catch (error) {
    throw new Error('Error: Unable to reach the server');
  }
}

// Checks if server reachable
async function reqPerm() {
  try {
    // Add the note to the deck
    const reqPermResponse = await fetch('http://localhost:8765', {
      method: 'POST',
      body: JSON.stringify({
        action: 'requestPermission',
        version: 6,
      }),
    });

    const jsonResponse = await reqPermResponse.json();
    return jsonResponse.result.permission;
  } catch (error) {
    return false
  }
}

/**
 * The component's render function. This will be called immediately after
 * the component is initially loaded, and then again every time the
 * component gets new data from Python.
 */
async function onRender(event: Event): Promise<void> {
  // Get the RenderData from the event
  const data = (event as CustomEvent<RenderData>).detail

  // RenderData.args is the JSON dictionary of arguments sent from the
  // Python script.
  let action = data.args["action"]
  let deck = data.args["deck"]
  let front = data.args["front"]
  let back = data.args["back"]
  let tags = data.args["tags"]

  if (action == "reqPerm") {
    try {    
      const permission = await reqPerm();
      Streamlit.setComponentValue(permission)
    } catch (error) {
      throw new Error
    }
  } else if (action == "addCard") {    
    try {    
      const success = await addFlashcard(deck, front, back, tags);
      Streamlit.setComponentValue(`Worked!, ${success}`)
    } catch (error) {
      throw new Error
    }
  } else {
    throw new Error
  }

  // We tell Streamlit to update our frameHeight after each render event, in
  // case it has changed. (This isn't strictly necessary for the example
  // because our height stays fixed, but this is a low-cost function, so
  // there's no harm in doing it redundantly.)
  Streamlit.setFrameHeight()
}

// Attach our `onRender` handler to Streamlit's render event.
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)

// Tell Streamlit we're ready to start receiving data. We won't get our
// first RENDER_EVENT until we call this function.
Streamlit.setComponentReady()

// Finally, tell Streamlit to update our initial height. We omit the
// `height` parameter here to have it default to our scrollHeight.
Streamlit.setFrameHeight()