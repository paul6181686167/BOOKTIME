import { bookRefToBookLike, toBookRef } from '../friendsService';

describe('livres recommandés entre amis', () => {
  it('construit une référence légère à partir d’un livre de la bibliothèque', () => {
    expect(
      toBookRef({
        id: 'b1',
        title: 'Dune',
        display_title: 'Dune (FR)',
        author: 'Frank Herbert',
        cover_image_url: 'https://x/c.jpg',
        category: 'roman',
        isbn: '9782266320795',
        status: 'completed',
        review: 'secret',
      })
    ).toEqual({
      title: 'Dune (FR)',
      author: 'Frank Herbert',
      cover_url: 'https://x/c.jpg',
      category: 'roman',
      ol_key: '',
      isbn: '9782266320795',
    });
    expect(toBookRef(null)).toBeNull();
  });

  it('transforme une référence reçue en livre à découvrir (non possédé)', () => {
    const book = bookRefToBookLike({ title: 'Dune', author: '', ol_key: '/works/OL1W' });
    expect(book.isFromOpenLibrary).toBe(true);
    expect(book.id).toBe('friend_/works/OL1W');
    expect(book.author).toBe('Auteur inconnu');
    expect(book.ol_key).toBe('/works/OL1W');
    expect(book.category).toBe('roman');
  });

  it('retombe sur l’isbn puis le titre pour fabriquer un identifiant', () => {
    expect(bookRefToBookLike({ title: 'A', author: 'B', isbn: '123' }).id).toBe('friend_123');
    expect(bookRefToBookLike({ title: 'A', author: 'B' }).id).toBe('friend_A|B');
  });
});
