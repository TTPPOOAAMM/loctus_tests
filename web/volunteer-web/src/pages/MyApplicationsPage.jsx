import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

function MyApplicationsPage() {
    const [applications, setApplications] = useState([]);
    const [locations, setLocations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const initPage = async () => {
            await fetchLocations();
            await fetchApplications();
        };
        initPage();
    }, []);

    const fetchLocations = async () => {
        try {
            const response = await api.get('/api/references/locations');
            setLocations(response.data);
        } catch (err) {
            console.error('Ошибка загрузки локаций', err);
        }
    };

    const fetchApplications = async () => {
        try {
            const response = await api.get('/api/applications/me');
            setApplications(response.data);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setError('Не удалось загрузить историю заявок.');
            setLoading(false);
        }
    };

    const getLocationName = (id) => {
        const loc = locations.find(l => l.ID_Locations === id);
        return loc ? loc.district_name : 'Локация не указана';
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'pending':
                return <span className="badge bg-warning text-dark px-3 py-2 fs-6">Ожидает рассмотрения</span>;
            case 'approved':
                return <span className="badge bg-success px-3 py-2 fs-6">Одобрена</span>;
            case 'rejected':
                return <span className="badge bg-danger px-3 py-2 fs-6">Отклонена</span>;
            case 'expired':
                return <span className="badge bg-secondary px-3 py-2 fs-6">Истекла (Набор закрыт)</span>;
            case 'completed':
                return <span className="badge bg-info px-3 py-2 fs-6">Завершена</span>;
            default:
                return <span className="badge bg-dark px-3 py-2 fs-6">{status}</span>;
        }
    };

    return (
        <div className="bg-light min-vh-100 pb-5">
            <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
                <div className="container">
                    <Link to="/" className="navbar-brand mb-0 h1 text-decoration-none">Волонтер Москвы</Link>
                    <div className="d-flex gap-3 align-items-center">
                        <Link to="/" className="text-white text-decoration-none">Доска</Link>
                        <Link to="/profile" className="text-white text-decoration-none">Мой профиль</Link>
                        <Link to="/my-applications" className="text-white fw-bold text-decoration-none">Мои заявки</Link>
                        <button className="btn btn-sm btn-outline-light" onClick={() => {
                            localStorage.removeItem('access_token');
                            window.location.href = '/auth';
                        }}>Выйти</button>
                    </div>
                </div>
            </nav>

            <div className="container mt-4">
                <h2 className="mb-4">Мои заявки</h2>

                {loading && <div className="text-center mt-5"><div className="spinner-border text-primary" role="status"></div></div>}
                {error && <div className="alert alert-danger">{error}</div>}

                {!loading && applications.length === 0 && !error && (
                    <div className="card shadow-sm border-0">
                        <div className="card-body text-center text-muted py-5">
                            <p className="mb-0 fs-5">Вы еще не откликались ни на одно мероприятие.</p>
                            <Link to="/" className="btn btn-primary mt-3">Перейти к Доске объявлений</Link>
                        </div>
                    </div>
                )}

                <div className="row g-4">
                    {applications.map((app) => (
                        <div key={app.ID_application} className="col-md-6">
                            <div className="card shadow-sm h-100 border-0">
                                <div className="card-body d-flex flex-column p-4">
                                    <h4 className="card-title text-primary fw-bold mb-3">
                                        {app.event.title}
                                    </h4>
                                    
                                    <div className="d-flex align-items-center mb-3 text-muted small">
                                        <span className="me-3">📅 {new Date(app.event.event_date).toLocaleDateString('ru-RU')}</span>
                                        <span>📍 {getLocationName(app.event.location_id)}</span>
                                    </div>

                                    <p className="card-text text-secondary flex-grow-1">
                                        {app.event.description || 'Описание мероприятия отсутствует.'}
                                    </p>

                                    <hr className="text-muted my-3" />

                                    <div className="d-flex justify-content-between align-items-center mt-auto">
                                        <div className="text-muted small">
                                            Подано: {new Date(app.applied_at).toLocaleDateString('ru-RU')}
                                        </div>
                                        <div>
                                            {getStatusBadge(app.status)}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default MyApplicationsPage;