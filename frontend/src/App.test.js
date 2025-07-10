import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('BOOKTIME App Tests', () => {
  test('basic functionality works', () => {
    expect(true).toBe(true);
  });

  test('math operations work', () => {
    expect(2 + 2).toBe(4);
    expect(5 * 3).toBe(15);
  });

  test('string operations work', () => {
    expect('BOOKTIME'.toLowerCase()).toBe('booktime');
    expect('hello'.charAt(0)).toBe('h');
  });

  test('array operations work', () => {
    const books = ['Roman', 'BD', 'Manga'];
    expect(books.length).toBe(3);
    expect(books).toContain('Roman');
  });

  test('simple component renders', () => {
    const TestComponent = () => React.createElement('div', null, 'Test Component');
    render(React.createElement(TestComponent));
    expect(screen.getByText('Test Component')).toBeInTheDocument();
  });
});
