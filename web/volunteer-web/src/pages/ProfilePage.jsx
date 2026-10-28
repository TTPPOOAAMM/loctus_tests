import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

function ProfilePage() {
    const [phone, setPhone] = useState('');
    const [birthDate, setBirthDate] = useState('');
    const [interests, setInterests] = useState('');
    const [skills, setSkills] = useState('');
    
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState({ text: '', type: '' });

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            const response = await api.get('/api/users/me');
            const profile = response.data.profile;
            if (profile) {
                setPhone(profile.phone || '');
                setBirthDate(profile.birth_date || '');
                setInterests(profile.interests || '');
                
                if (profile.skills && profile.skills.length > 0) {
                    setSkills(profile.skills.map(s => s.skill_name).join(', '));
                }
            }
            setLoading(false);
        } catch (err) {
            console.error(err);
            setMessage({ text: 'Не удалось загрузить данные профиля.', type: 'danger' });
            setLoading(false);
        }
    };

    const validatePhone = (phoneNumber) => {
        if (!phoneNumber) return true; 
        const phoneRegex = /^\+?[0-9\s\-\(\)]{10,18}$/;
        return phoneRegex.test(phoneNumber);
    };

    const validateBirthDate = (dateString) => {
        if (!dateString) return true;
        const selectedDate = new Date(dateString);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        return selectedDate < today;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage({ text: '', type: '' });

        if (!validatePhone(phone)) {
            setMessage({ text: 'Некорректный формат телефона. Пример: 89991234567', type: 'danger' });
            return;
        }

        if (!validateBirthDate(birthDate)) {
            setMessage({ text: 'Дата рождения не может быть сегодняшним днем или в будущем.', type: 'danger' });
            return;
        }

        const skillsArray = skills.split(',')
                                  .map(s => s.trim())
                                  .filter(s => s !== '');

        try {
            await api.put('/api/users/me/profile', {
                phone: phone || null,
                birth_date: birthDate || null,
                interests: interests || null,
                skills: skillsArray
            });
            setMessage({ text: 'Профиль успешно обновлен!', type: 'success' });
        } catch (err) {
            setMessage({ text: 'Ошибка при сохранении профиля на сервере.', type: 'danger' });
        }
    };

    if (loading) return <div className="text-center mt-5"><div className="spinner-border text-primary" role="status"></div></div>;

    return (
        <div className="bg-light min-vh-100">
            <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
                <div className="container">
                    <Link to="/" className="navbar-brand mb-0 h1 text-decoration-none">Волонтер Москвы</Link>
                    <div className="d-flex gap-3 align-items-center">
                        <Link to="/" className="text-white text-decoration-none">Доска</Link>
                        <Link to="/profile" className="text-white fw-bold text-decoration-none">Мой профиль</Link>
                        <Link to="/my-applications" className="text-white text-decoration-none">Мои заявки</Link>
                        <button className="btn btn-sm btn-outline-light" onClick={() => {
                            localStorage.removeItem('access_token');
                            window.location.href = '/auth';
                        }}>Выйти</button>
                    </div>
                </div>
            </nav>

            <div className="container mt-4">
                <div className="row justify-content-center">
                    <div className="col-md-8 col-lg-6">
                        <div className="card shadow-sm">
                            <div className="card-body p-4">
                                <h3 className="mb-4">Моя анкета</h3>
                                
                                {message.text && (
                                    <div className={`alert alert-${message.type}`} role="alert">
                                        {message.text}
                                    </div>
                                )}

                                <form onSubmit={handleSubmit}>
                                    <div className="mb-3">
                                        <label className="form-label">Телефон</label>
                                        <input 
                                            type="text" 
                                            className="form-control" 
                                            value={phone} 
                                            onChange={(e) => setPhone(e.target.value)} 
                                            placeholder="89990000000" 
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label">Дата рождения</label>
                                        <input 
                                            type="date" 
                                            className="form-control" 
                                            value={birthDate} 
                                            onChange={(e) => setBirthDate(e.target.value)} 
                                        />
                                    </div>
                                    <div className="mb-3">
                                        <label className="form-label">Интересы (о себе)</label>
                                        <textarea 
                                            className="form-control" 
                                            rows="3" 
                                            value={interests} 
                                            onChange={(e) => setInterests(e.target.value)} 
                                            placeholder="Например: Люблю помогать животным..."
                                        ></textarea>
                                    </div>
                                    <div className="mb-4">
                                        <label className="form-label">Навыки (через запятую)</label>
                                        <input 
                                            type="text" 
                                            className="form-control" 
                                            value={skills} 
                                            onChange={(e) => setSkills(e.target.value)} 
                                            placeholder="Фотография, Первая помощь, Английский язык" 
                                        />
                                    </div>
                                    <button type="submit" className="btn btn-primary w-100">Сохранить изменения</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ProfilePage;