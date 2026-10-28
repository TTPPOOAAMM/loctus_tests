// src/pages/HomePage.jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

function HomePage() {
    const [events, setEvents] = useState([]);
    const [locations, setLocations] = useState([]); // Стейт для справочника локаций
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Стейты для панели фильтрации
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedLocation, setSelectedLocation] = useState('');
    const [sortOrder, setSortOrder] = useState('asc'); // asc = сначала ближайшие

    useEffect(() => {
        // При первой загрузке стягиваем справочник локаций и список мероприятий
        fetchLocations();
        fetchEvents();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const fetchLocations = async () => {
        try {
            const response = await api.get('/api/references/locations');
            setLocations(response.data);
        } catch (err) {
            console.error('Ошибка загрузки локаций', err);
        }
    };

    const fetchEvents = async (e) => {
        if (e) e.preventDefault(); // Если вызвано из формы, предотвращаем перезагрузку страницы
        setLoading(true);
        setError('');
        
        try {
            // Формируем параметры запроса к нашему FastAPI бэкенду
            const params = new URLSearchParams();
            if (searchQuery) params.append('search', searchQuery);
            if (selectedLocation) params.append('location_id', selectedLocation);

            // Бэкенд сам отфильтрует данные
            const response = await api.get('/api/events/', { params });
            let fetchedEvents = response.data;

            // Бэкенд возвращает отсортированные по возрастанию даты (asc).
            // Добавляем логику реверсивной сортировки на фронтенде:
            if (sortOrder === 'desc') {
                fetchedEvents.sort((a, b) => new Date(b.event_date) - new Date(a.event_date));
            } else {
                fetchedEvents.sort((a, b) => new Date(a.event_date) - new Date(b.event_date));
            }

            setEvents(fetchedEvents);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setError('Не удалось загрузить мероприятия');
            setLoading(false);
        }
    };

    const handleApply = async (eventId) => {
        try {
            await api.post('/api/applications/', { event_id: eventId });
            alert('Заявка успешно подана!');
        } catch (err) {
            alert(err.response?.data?.detail || 'Ошибка при подаче заявки');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        window.location.href = '/auth';
    };

    // Вспомогательная функция, чтобы превратить location_id в красивое название района
    const getLocationName = (id) => {
        const loc = locations.find(l => l.ID_Locations === id);
        return loc ? loc.district_name : 'Локация не указана';
    };

    return (
        <div className="bg-light min-vh-100 pb-5">
            <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
                <div className="container">
                    <Link to="/" className="navbar-brand mb-0 h1 text-decoration-none">Волонтер Москвы</Link>
                    <div className="d-flex gap-3 align-items-center">
                        <Link to="/profile" className="text-white text-decoration-none">Мой профиль</Link>
                        <Link to="/my-applications" className="text-white text-decoration-none">Мои заявки</Link>
                        <button className="btn btn-sm btn-outline-light" onClick={handleLogout}>Выйти</button>
                    </div>
                </div>
            </nav>

            <div className="container mt-4">
                <h2 className="mb-4">Доска мероприятий</h2>

                {/* ПАНЕЛЬ ФИЛЬТРАЦИИ */}
                <div className="card shadow-sm mb-4">
                    <div className="card-body">
                        <form onSubmit={fetchEvents} className="row g-3 align-items-end">
                            <div className="col-md-4">
                                <label className="form-label text-muted small mb-1">Поиск по названию</label>
                                <input 
                                    type="text" 
                                    className="form-control" 
                                    placeholder="Например: Посадка деревьев" 
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>
                            <div className="col-md-3">
                                <label className="form-label text-muted small mb-1">Район (Локация)</label>
                                <select 
                                    className="form-select" 
                                    value={selectedLocation}
                                    onChange={(e) => setSelectedLocation(e.target.value)}
                                >
                                    <option value="">Все районы</option>
                                    {locations.map(loc => (
                                        <option key={loc.ID_Locations} value={loc.ID_Locations}>
                                            {loc.district_name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="col-md-3">
                                <label className="form-label text-muted small mb-1">Сортировка</label>
                                <select 
                                    className="form-select" 
                                    value={sortOrder}
                                    onChange={(e) => setSortOrder(e.target.value)}
                                >
                                    <option value="asc">Сначала ближайшие</option>
                                    <option value="desc">Сначала поздние</option>
                                </select>
                            </div>
                            <div className="col-md-2">
                                <button type="submit" className="btn btn-primary w-100">
                                    Найти
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                {/* ВЫВОД ОШИБОК И ЗАГРУЗКИ */}
                {loading && <div className="text-center mt-5"><div className="spinner-border text-primary" role="status"></div></div>}
                {error && <div className="alert alert-danger">{error}</div>}

                {/* СЕТКА КАРТОЧЕК */}
                <div className="row g-4">
                    {!loading && events.length === 0 && !error && (
                        <div className="col-12 text-center text-muted py-5">
                            <p>По вашему запросу ничего не найдено.</p>
                        </div>
                    )}

                    {events.map((event) => (
                        <div key={event.ID_event} className="col-md-6 col-lg-4">
                            <div className="card h-100 shadow-sm border-0">
                                <div className="card-body d-flex flex-column">
                                    <h5 className="card-title text-primary fw-bold">{event.title}</h5>
                                    
                                    <div className="d-flex align-items-center mb-2 text-muted small">
                                        <span className="me-3">📅 {new Date(event.event_date).toLocaleDateString('ru-RU')}</span>
                                        <span>📍 {getLocationName(event.location_id)}</span>
                                    </div>

                                    <p className="card-text flex-grow-1 mt-2">
                                        {event.description || 'Описание отсутствует.'}
                                    </p>
                                    
                                    <div className="mb-3 text-muted small bg-light p-2 rounded">
                                        <strong>Осталось мест:</strong> {event.max_participants}
                                    </div>
                                    
                                    <button 
                                        className="btn btn-outline-primary w-100 mt-auto"
                                        onClick={() => handleApply(event.ID_event)}
                                    >
                                        Откликнуться
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default HomePage;