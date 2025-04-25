import React, { useState } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [sqlResult, setSqlResult] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);  // Додано для помилок

  // Обробка відправки запиту
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);  // Скидаємо помилки перед кожним запитом

    async function fetchData() {
      try {
        console.log("Sending query:", query); // Додано логування

        const response = await fetch("http://127.0.0.1:5000/post_movies", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ query })
        });

        const data = await response.json();
        console.log(data);
        
        // Перевірка на помилки у відповіді
        if (data.error) {
          throw new Error(data.error);  // Генерація помилки, якщо є
        }
        
        // Оновлення стану результатів
        setSqlResult(data.generated_sql);
        setResults(data.results);
      } catch (error) {
        console.error("Error:", error);
        setError(error.message);  // Встановлюємо помилку в стан
      } finally {
        setLoading(false);  // Завершуємо завантаження
      }
    }

    fetchData(); // Викликаємо функцію для виконання запиту
  };

  return (
    <div className="App" style={{ backgroundColor: "#d1f2eb", padding: "10px" }}>
      <h1 style={{color: "#0b5345"}}>Ask me about movies and actors</h1>
      <b>You can ask me smth like:</b>
      <p style={{fontStyle:"italic"}}>Show movies with Robert Downey Jr.</p>
      <p style={{fontStyle:"italic"}}>Show actors in Titanic</p>
      <br /><br />
      
      <form onSubmit={handleSubmit}>
        <input 
          type="text" 
          value={query} 
          onChange={(e) => setQuery(e.target.value)} 
          placeholder="Write your request ..." 
        />
        <button type="submit" disabled={loading}>Send</button>
      </form>

      {loading && <p>Wait, please...</p>}
      
      {error && (
        <div style={{color: "red"}}>
          <p>Error: {error}</p>
        </div>
      )}

      {sqlResult && (
        <div>
          <h2 style={{ color: "#0e6655" }}>Generated SQL:</h2>
          <pre>{sqlResult}</pre>
        </div>
      )}

      {results.length > 0 && (
        <div>
          <h2 style={{ color: "#0e6655" }}>Results:</h2>
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
