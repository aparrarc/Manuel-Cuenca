import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import ManuelCuencaLanding from './pages/ManuelCuencaLanding';
import ManuelCuencaBooking from './pages/ManuelCuencaBooking';

function App() {
    return <BrowserRouter>
        <Routes>
            <Route path="/" element={<ManuelCuencaLanding />} />
            <Route path="/booking" element={<ManuelCuencaBooking />} />
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    </BrowserRouter>;
}

export default App;
