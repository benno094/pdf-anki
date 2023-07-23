// Need to implement method to see if API is running

async function addFlashcard() {
    const deckName: string = 'MyDeck';
    const front: string = 'Front of the card';
    const back: string = 'Back of the card';
  
    try {
      // Call the API using TypeScript fetch()
      const createDeckResponse = await fetch('http://localhost:8765', {
        method: 'POST',
        body: JSON.stringify({
          action: 'createDeck',
          params: { deck: deckName },
          version: 6,
        }),
      });
  
      // Add the note to the deck
      const note = {
        deckName: deckName,
        modelName: 'Basic',
        fields: { Front: front, Back: back },
        options: { allowDuplicate: false },
        tags: [],
      };
      const addNoteResponse = await fetch('http://localhost:8765', {
        method: 'POST',
        body: JSON.stringify({
          action: 'addNote',
          params: { note: note },
          version: 6,
        }),
      });
  
      const result = await addNoteResponse.json();
      console.log(result);
    } catch (error) {
      console.error(error);
    }
  }