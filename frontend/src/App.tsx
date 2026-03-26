import { BrowserRouter, Routes, Route } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<div>Voice Map — Coming Soon</div>} />
        {/* <Route path="/login" element={<LoginPage />} /> */}
        {/* <Route path="/chat" element={<ChatRoom />} /> */}
      </Routes>
    </BrowserRouter>
  );
}

export default App;
