import { useState } from 'react';
import api from '../api';

function AuthPage() {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        try {
            if (isLogin) {
                const params = new URLSearchParams();
                params.append('username', email);
                params.append('password', password);

                const response = await api.post('/api/auth/login', params);
                localStorage.setItem('access_token', response.data.access_token);
                window.location.href = '/'; 
            } else {
                await api.post('/api/auth/register', {
                    full_name: fullName,
                    email: email,
                    password: password,
                    role_id: 1
                });
                
                alert("Регистрация успешна! Теперь войдите.");
                setIsLogin(true);
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Произошла ошибка');
        }
    };

    return (
        <div className="container mt-5">
            <div className="row justify-content-center">
                <div className="col-md-6 col-lg-4">
                    <div className="card shadow-sm">
                        <div className="card-body p-4">
                            <h3 className="text-center mb-4">
                                {isLogin ? 'Вход для Волонтеров' : 'Регистрация'}
                            </h3>
                            
                            {error && (
                                <div className="alert alert-danger" role="alert">
                                    {error}
                                </div>
                            )}

                            <form onSubmit={handleSubmit}>
                                {!isLogin && (
                                    <div className="mb-3">
                                        <label className="form-label">ФИО</label>
                                        <input 
                                            type="text" 
                                            className="form-control"
                                            value={fullName} 
                                            onChange={(e) => setFullName(e.target.value)} 
                                            required 
                                        />
                                    </div>
                                )}
                                
                                <div className="mb-3">
                                    <label className="form-label">Email</label>
                                    <input 
                                        type="email" 
                                        className="form-control"
                                        value={email} 
                                        onChange={(e) => setEmail(e.target.value)} 
                                        required 
                                    />
                                </div>
                                
                                <div className="mb-4">
                                    <label className="form-label">Пароль</label>
                                    <input 
                                        type="password" 
                                        className="form-control"
                                        value={password} 
                                        onChange={(e) => setPassword(e.target.value)} 
                                        required 
                                    />
                                </div>
                                
                                <button type="submit" className="btn btn-primary w-100 mb-3">
                                    {isLogin ? 'Войти' : 'Зарегистрироваться'}
                                </button>
                            </form>

                            <div className="text-center">
                                <button 
                                    className="btn btn-link text-decoration-none" 
                                    onClick={() => setIsLogin(!isLogin)}
                                >
                                    {isLogin ? 'Нет аккаунта? Зарегистрируйтесь' : 'Уже есть аккаунт? Войти'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AuthPage;