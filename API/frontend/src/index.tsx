import { Streamlit, RenderData } from "streamlit-component-lib"
import CryptoES from 'crypto-es';

// TODO: Add tablet functionality using URL-schemes
// Force sync after adding

// TODO: Publish separate component

interface Card {
  front: string;
  back: string;
  filename: string;
  tags: string[];
  image: string;
}

// Adds note to a deck

async function storeImage(image: string, filename: string) {
    try {
        console.log("Storing image with filename:", filename); // Debug log
        // Store the image in Anki's media collection
        const storeMediaResponse = await fetch("http://localhost:8765", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                action: "storeMediaFile",
                version: 6,
                params: {
                    filename: filename,
                    data: image // Use the base64-encoded image directly
                }
            })
        });

        const storeMediaJson = await storeMediaResponse.json();
        console.log("Store Media Response:", storeMediaJson); // Debug log

        if (storeMediaJson.error) {
            console.error(`Error storing image: ${storeMediaJson.error}`);
            Streamlit.setComponentValue(`Error storing image: ${storeMediaJson.error}`);
            return `Error storing image: ${storeMediaJson.error}`;
        }

        console.log(`Image successfully stored with filename: ${filename}`);
        Streamlit.setComponentValue(`Image successfully stored with filename: ${filename}`);
        return storeMediaJson.result;
    } catch (error) {
        throw new Error('Error: Unable to reach the server');
        return "Error";
    }
}

async function addFlashcard(deck: string, front: string, back: string, tags: string) {
  try {
    const note = {
      deckName: deck,
      modelName: 'AnKingOverhaul',
      fields: { Text: front, Extra: back },
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

    const jsonResponse = await addNoteResponse.json();
    return jsonResponse.result;
  } catch (error) {
    throw new Error('Error: Unable to reach the server');
  }
}

// Adds note to a deck
async function addFlashcards(deck: string, flashcards: Card[]) {
  try {
    const notes = await Promise.all(flashcards.map(async (card) => {
      let note = {
        deckName: deck,
        modelName: 'AnKingOverhaul',
        fields: { Text: card.front, Extra: card.back },
        options: { allowDuplicate: false },
        tags: card.tags,
        picture: undefined as any  // Initialize picture as undefined
      };

      if (card.image) {
        let date = Date.now();
        let hash = CryptoES.SHA256(date.toString()).toString();
        let filename = "pdf-anki-" + hash + ".jpg";

        // Save the image file
        note.picture = [{
          data: card.image,  // Use the image data directly here
          filename: filename,
          fields: []
        }];

        // Include the image using an HTML <img> tag in the 'Back' field
        note.fields.Extra = card.back + `<br><img src="${filename}" />`;
      }

      return note;
    }));

    const addNotesResponse = await fetch('http://localhost:8765', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        action: 'addNotes',
        version: 6,
        params: { notes }
      }),
    });

    const jsonResponse = await addNotesResponse.json();

    if (jsonResponse.error) {
      throw new Error(jsonResponse.error);
    }

    return jsonResponse.result;
  } catch (error) {
    throw new Error('Error: Unable to reach the server');
  }
}

// Adds note to a deck including image
async function addFlashcardWithImage(deck: string, image: string, front: string, back: string, tags: string) {
  let date = Date.now();
  let hash = CryptoES.SHA256(date.toString());
  try {
    const note = {
      deckName: deck,
      modelName: 'AnKingOverhaul',
      fields: { Text: front, Extra: back },
      options: { allowDuplicate: false },
      tags: [ tags ],
      picture: [{
        data: image,
        filename: "pdf-anki-" + hash + ".jpg",
        fields: [ "Extra" ]
      }]
    };
    const addNoteResponse = await fetch('http://localhost:8765', {
      method: 'POST',
      body: JSON.stringify({
        action: 'addNotes',
        params: { note: note },
        version: 6,
      }),
    });

    const jsonResponse = await addNoteResponse.json();
    return jsonResponse.result;
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

async function checkModelExistence() {
  try {
    // Add the note to the deck
    const checkModelExistence = await fetch('http://localhost:8765', {
      method: 'POST',
      body: JSON.stringify({
        action: 'modelNames',
        version: 6,
      }),
    });

    const jsonResponse = await checkModelExistence.json();
    if (!jsonResponse.result.includes("AnKingOverhaul")) {
      const createModel = await fetch('http://localhost:8765', {
      method: 'POST',
      body: JSON.stringify({
        action: "createModel",
        version: 6,
        params: {
          modelName: "AnKingOverhaul",
          inOrderFields: ["Text", "Extra"],
          isCloze: true,
          cardTemplates: [
            {
              Name: "Cloze",
              Front: "{{cloze:Text}}",
              Back: "{{cloze:Text}}\n\n<hr id=answer>\n\n{{Extra}}<br><br>\n\nTags: {{Tags}}",
            },
          ],
        },
      }),
    });

    const jsonResponse = await createModel.json();
    return jsonResponse.result;
    }
  } catch (error) {
    return false
  }
}

// Returns users decks
async function getDecks() {
  try {
    // Add the note to the deck
    const getDecksResponse = await fetch('http://localhost:8765', {
      method: 'POST',
      body: JSON.stringify({
        action: 'deckNames',
        version: 6,
      }),
    });

    const jsonResponse = await getDecksResponse.json();
    return jsonResponse.result;
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
  let image = data.args["image"]
  let front = data.args["front"]
  let back = data.args["back"]
  let tags = data.args["tags"]
  let flashcards = data.args["flashcards"]
  let filename = data.args["filename"];

  try {
    switch (action) {
      case "reqPerm":
        // Initialization for checking if server reachable and model exists
        await reqPerm();
        const checkModel = await checkModelExistence();
        Streamlit.setComponentValue(checkModel)
        break;
      case "addCard":
        const success = await addFlashcard(deck, front, back, tags);
        Streamlit.setComponentValue(success)
        break;
      case "addNotes":
        const cards = await addFlashcards(deck, flashcards);
        Streamlit.setComponentValue(cards)
        break;
      case "storeImage":
        const storeImageResult = await storeImage(image, filename);
        Streamlit.setComponentValue(storeImageResult);
      case "addCardWithImage":
        const response = await addFlashcardWithImage(deck, image, front, back, tags);
        Streamlit.setComponentValue(response)
        break;
      case "getDecks":
        const decks = await getDecks();
        Streamlit.setComponentValue(decks)
        break;
    }
  } catch (error) {
    Streamlit.setComponentValue("Error")
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