import pytest
import json
from unittest.mock import patch, MagicMock
import sqlite3
from movies import app, is_safe_sql


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_db_connection():
    """Фікстура для моку з'єднання з базою даних"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Патчимо sqlite3.connect, щоб повертав наш мок
    with patch('sqlite3.connect', return_value=mock_conn):
        yield mock_cursor


def test_hello(client):
    """Тест привітального ендпоінту"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello from your Flask API' in response.data


def test_get_actors(client, mock_db_connection):
    """Тест ендпоінту для отримання акторів"""
    # Налаштовуємо мок для повернення тестових даних
    mock_data = [(1, 'Tom Hanks'), (2, 'Brad Pitt')]
    mock_db_connection.fetchall.return_value = mock_data
    
    response = client.get('/actors')
    assert response.status_code == 200
    
    # Перевіряємо, що правильний SQL запит був виконаний
    mock_db_connection.execute.assert_called_once_with("SELECT * FROM Actors")
    
    # Перевіряємо відповідь
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0][0] == 1
    assert data[0][1] == 'Tom Hanks'


def test_get_movies(client, mock_db_connection):
    """Тест ендпоінту для отримання фільмів"""
    # Налаштовуємо мок для повернення тестових даних
    mock_data = [(1, 'The Shawshank Redemption'), (2, 'The Godfather')]
    mock_db_connection.fetchall.return_value = mock_data
    
    response = client.get('/movies')
    assert response.status_code == 200
    
    # Перевіряємо, що правильний SQL запит був виконаний
    mock_db_connection.execute.assert_called_once_with("SELECT * FROM Movies")
    
    # Перевіряємо відповідь
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0][0] == 1
    assert data[0][1] == 'The Shawshank Redemption'


@patch('openai.chat.completions.create')
def test_natural_language_to_sql_success(mock_openai, client, mock_db_connection):
    """Інтеграційний тест для ендпоінту natural_language_to_sql з моком OpenAI API"""
    # Налаштування мока для OpenAI
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "SELECT * FROM Movies WHERE id = 1"
    mock_openai.return_value = mock_response
    
    # Налаштовуємо мок для бази даних
    mock_db_connection.fetchall.return_value = [(1, 'The Shawshank Redemption')]
    
    # Відправляємо тестовий запит
    response = client.post('/post_movies', 
                          data=json.dumps({'query': 'Show movie with id 1'}),
                          content_type='application/json')
    
    # Перевіряємо результат
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'generated_sql' in data
    assert data['generated_sql'] == "SELECT * FROM Movies WHERE id = 1"
    assert data['results'] == [[1, 'The Shawshank Redemption']]
    
    # Перевіряємо, що OpenAI API був викликаний
    mock_openai.assert_called_once()


@patch('openai.chat.completions.create')
def test_natural_language_to_sql_unsafe(mock_openai, client):
    """Тест обробки небезпечного SQL запиту"""
    # Налаштування мока для OpenAI, що повертає небезпечний SQL
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "DROP TABLE Movies"
    mock_openai.return_value = mock_response
    
    # Відправляємо тестовий запит
    response = client.post('/post_movies', 
                          data=json.dumps({'query': 'Delete all movies'}),
                          content_type='application/json')
    
    # Перевіряємо результат - має бути помилка
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Unsafe SQL detected'


def test_natural_language_to_sql_missing_query(client):
    """Тест обробки запиту без параметра query"""
    response = client.post('/post_movies', 
                          data=json.dumps({}),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Missing query'


@patch('openai.chat.completions.create')
def test_natural_language_to_sql_db_error(mock_openai, client):
    """Тест обробки помилки бази даних"""
    # Налаштування мока для OpenAI
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "SELECT * FROM NonExistentTable"
    mock_openai.return_value = mock_response
    
    # Відправляємо тестовий запит, який викличе помилку при виконанні SQL
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.OperationalError("no such table: NonExistentTable")
        mock_connect.return_value = mock_conn
        
        response = client.post('/post_movies', 
                              data=json.dumps({'query': 'Show data from non-existent table'}),
                              content_type='application/json')
    
    # Перевіряємо результат - має бути помилка
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'no such table' in data['error']


def test_is_safe_sql():
    """Тести для функції перевірки безпеки SQL"""
    # Безпечні запити
    assert is_safe_sql("SELECT * FROM Movies") == True
    assert is_safe_sql("SELECT name FROM Actors WHERE id = 1") == True
    
    # Небезпечні запити
    assert is_safe_sql("DROP TABLE Movies") == False
    assert is_safe_sql("DELETE FROM Actors") == False
    assert is_safe_sql("INSERT INTO Movies VALUES (1, 'Test')") == False
    assert is_safe_sql("UPDATE Actors SET name = 'Test' WHERE id = 1") == False
    assert is_safe_sql("SELECT * FROM Movies; DROP TABLE Movies") == False
