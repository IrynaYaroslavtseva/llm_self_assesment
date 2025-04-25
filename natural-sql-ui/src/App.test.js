import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

// Мокуємо fetch API
global.fetch = jest.fn();

describe('App Component', () => {
  beforeEach(() => {
    // Очищаємо моки перед кожним тестом
    fetch.mockClear();
  });

  test('renders the app title', () => {
    render(<App />);
    const titleElement = screen.getByText(/Ask me about movies and actors/i);
    expect(titleElement).toBeInTheDocument();
  });

  test('renders example queries', () => {
    render(<App />);
    expect(screen.getByText(/Show movies with Robert Downey Jr./i)).toBeInTheDocument();
    expect(screen.getByText(/Show actors in Titanic/i)).toBeInTheDocument();
  });

  test('has input field and submit button', () => {
    render(<App />);
    expect(screen.getByPlaceholderText(/Write your request/i)).toBeInTheDocument();
    expect(screen.getByText(/Send/i)).toBeInTheDocument();
  });

  test('updates query state when typing', () => {
    render(<App />);
    const inputElement = screen.getByPlaceholderText(/Write your request/i);
    
    fireEvent.change(inputElement, { target: { value: 'Show all movies' } });
    
    expect(inputElement.value).toBe('Show all movies');
  });

  test('submits form and shows loading state', async () => {
    // Мокуємо відповідь від API
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => {
        // Не вирішуємо проміс, щоб залишитися в стані завантаження
        setTimeout(() => {}, 1000);
      })
    );
    
    render(<App />);
    
    const inputElement = screen.getByPlaceholderText(/Write your request/i);
    const buttonElement = screen.getByText(/Send/i);
    
    fireEvent.change(inputElement, { target: { value: 'Show all movies' } });
    fireEvent.click(buttonElement);
    
    // Перевіряємо, що показується індикатор завантаження
    expect(screen.getByText(/Wait, please/i)).toBeInTheDocument();
  });

  test('shows SQL results after successful query', async () => {
    // Мокуємо успішну відповідь від API
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        json: () => Promise.resolve({
          generated_sql: 'SELECT * FROM Movies',
          results: [
            [1, 'The Shawshank Redemption'],
            [2, 'The Godfather']
          ]
        })
      })
    );
    
    render(<App />);
    
    const inputElement = screen.getByPlaceholderText(/Write your request/i);
    const buttonElement = screen.getByText(/Send/i);
    
    fireEvent.change(inputElement, { target: { value: 'Show all movies' } });
    fireEvent.click(buttonElement);
    
    // Чекаємо, поки результати з'являться
    await waitFor(() => {
      expect(screen.getByText(/Generated SQL:/i)).toBeInTheDocument();
      expect(screen.getByText(/SELECT \* FROM Movies/i)).toBeInTheDocument();
    });
    
    // Перевіряємо результати
    await waitFor(() => {
      expect(screen.getByText(/Results:/i)).toBeInTheDocument();
      expect(screen.getByText(/The Shawshank Redemption/i)).toBeInTheDocument();
      expect(screen.getByText(/The Godfather/i)).toBeInTheDocument();
    });
  });

  test('shows error message when API returns an error', async () => {
    // Мокуємо відповідь з помилкою
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        json: () => Promise.resolve({
          error: 'Invalid SQL query'
        })
      })
    );
    
    render(<App />);
    
    const inputElement = screen.getByPlaceholderText(/Write your request/i);
    const buttonElement = screen.getByText(/Send/i);
    
    fireEvent.change(inputElement, { target: { value: 'Invalid query' } });
    fireEvent.click(buttonElement);
    
    // Чекаємо, поки помилка з'явиться
    await waitFor(() => {
      expect(screen.getByText(/Error:/i)).toBeInTheDocument();
      expect(screen.getByText(/Invalid SQL query/i)).toBeInTheDocument();
    });
  });

  test('handles network error', async () => {
    // Мокуємо мережеву помилку
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('Network error'))
    );
    
    render(<App />);
    
    const inputElement = screen.getByPlaceholderText(/Write your request/i);
    const buttonElement = screen.getByText(/Send/i);
    
    fireEvent.change(inputElement, { target: { value: 'Show all movies' } });
    fireEvent.click(buttonElement);
    
    // Чекаємо, поки помилка з'явиться
    await waitFor(() => {
      expect(screen.getByText(/Error:/i)).toBeInTheDocument();
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });

  test('sends correct request to API', async () => {
    // Мокуємо відповідь від API
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        json: () => Promise.resolve({
          generated_sql: 'SELECT * FROM Movies',
          results: []
        })
      })
    );
    
    render(<App />);
    
    const inputElement = screen.getByPlaceholderText(/Write your request/i);
    const buttonElement = screen.getByText(/Send/i);
    
    fireEvent.change(inputElement, { target: { value: 'Show all movies' } });
    fireEvent.click(buttonElement);
    
    // Перевіряємо, що fetch був викликаний з правильними параметрами
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:5000/post_movies',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'Show all movies' })
      })
    );
  });
});
