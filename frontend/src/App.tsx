import React, { useState } from "react";
import Chat from "./components/Chat";

const App: React.FC = () => {
  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <header style={{ padding: "1rem", background: "#3b82f6", color: "white" }}>
        <h1>Travel Chatbot</h1>
      </header>
      <main style={{ flex: 1, overflow: "hidden" }}>
        <Chat />
      </main>
    </div>
  );
};

export default App; 