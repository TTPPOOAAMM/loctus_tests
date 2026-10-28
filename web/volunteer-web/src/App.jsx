import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import MyApplicationsPage from './pages/MyApplicationsPage';

function App() {
    const isAuthenticated = !!localStorage.getItem('access_token');

    return (
        <Router>
            <Routes>
                <Route path="/auth" element={<AuthPage />} />
                
                <Route path="/" element={isAuthenticated ? <HomePage /> : <Navigate to="/auth" replace />} />

                <Route path="/profile" element={isAuthenticated ? <ProfilePage /> : <Navigate to="/auth" replace />} />

                <Route path="/my-applications" element={isAuthenticated ? <MyApplicationsPage /> : <Navigate to="/auth" replace />} />
            </Routes>
        </Router>
    );
}

export default App;