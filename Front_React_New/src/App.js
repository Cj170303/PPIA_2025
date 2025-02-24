import { React, useState, useRef, useEffect } from "react";
import TextField from "@mui/material/TextField";
import authConf from "./authConf.json";
import "./App.css";

function App() {
  const [studentNumber, setStudentNumber] = useState('')
  const [password, setPassword] = useState('')
  const [connected, setConnected] = useState(false)

  const [responseStudent, setResponseStudent] = useState([])
  const [chatHistory, setChatHistory] = useState([[]])
  const [currentChatHistory, setCurrentChatHistory] = useState({ conversation: [], conversationIndex: -1 });

  const chatHistoryRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleError = (errorMessage) => {
    setError(errorMessage);
  };

  const handleClose = () => {
    setError(null);
  };

  function ErrorModal({ error, onClose }) {
    return (
      <div className="modal">
        <div className="modal-content">
          <span className="close" onClick={onClose}>&times;</span>
          <p>{error}</p>
        </div>
      </div>
    );
  }
  
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
        const response = await fetch("/authConf.json");
        const authData = await response.json();
        const userExists = authData.users.some(
            user => user.studentNumber === studentNumber && user.password === password
        );
        if (userExists) {
            setConnected(true);
        } else {
            console.log("Nombre de usuario o contraseña incorrectos.");
        }
    } catch (error) {
        console.error("Error cargando authConf.json:", error);
    }
};

  const fetchChatHistory = async () => {
    try {
      const response = await fetch('History.json');
      const data = await response.json();
      if (data[0].length === 0) {
        setChatHistory([]);
        setCurrentChatHistory({ conversationIndex: 0, conversation: [] });
      } else {
        setChatHistory(data);
        setCurrentChatHistory({ 
          conversationIndex: data.length - 1, 
          conversation: data[data.length - 1] 
        });
      }
    } catch (error) {
      console.error('Error fetching chat history:', error);
    }
  };


  const inputHandler = (e) => {
    const userInput = e.target.value;
    setResponseStudent(userInput);
  };

  
  // Submission of the query to the back API
  const handleSubmit = () => {
    setLoading(true);
    const jsonData = {
      responseStudent: responseStudent,
      history: currentChatHistory.conversation,
    };
  
    fetch('api/query', {
      method: 'POST', 
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(jsonData),
    })
    .then(response => response.json())
    .then(data => {
      setLoading(false);
      if (data.message.responseChatbot === "reinit") {
        fetchChatHistory();
      } else {
        setCurrentChatHistory(prevHistory => ({conversation:
          [
          ...(prevHistory.conversation || []),
          { id: data.message.id, responseStudent: responseStudent, responseChatbot: data.message.responseChatbot}
          ],
          conversationIndex: prevHistory.conversationIndex })
        );
        

        // Update  the global chat history to avoid incoherences
        if (currentChatHistory.conversation===undefined || currentChatHistory.conversation.length===0){
          setChatHistory([...chatHistory, [{ id: data.message.id, responseStudent: responseStudent, responseChatbot: data.message.responseChatbot}]]);
        } else {
          const updatedHistory = chatHistory.map((conversation, index) => {
            if (index === currentChatHistory.conversationIndex) {
              return [...currentChatHistory.conversation, { id: data.message.id, responseStudent: responseStudent, responseChatbot: data.message.responseChatbot}];
            }
            return conversation;
          });
          setChatHistory(updatedHistory);
        }
        // Clear the TextField
        setResponseStudent('');
      }
    })
    .catch(error => {
      console.error('Error while sending the request to the backend: ', error);
      handleError("Ha ocurrido un error: por favor verifica que su pregunta no esté vacía.");
      setLoading(false);
    });
  };

  const isImageUrl = (url) => {
    return /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(url);
  };
  

  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [chatHistory]);
  
  useEffect(() => {
    fetchChatHistory();
  }, []);   

  if (!connected){
    return(<div className="container-form"> <form  id="msform"><fieldset><h2>Por favor, autentíquese </h2>
      <p><input type="text" value={studentNumber} onChange={(e) => setStudentNumber(e.target.value)} placeholder="Número estudiante"/></p>
      <p><input type="password" value={password} onChange={(e)=>setPassword(e.target.value)} placeholder="Contraseña"/></p>
      <button className="saveHistory-button" onClick={handleLogin}>Entrar</button>
  </fieldset></form></div>);
  }

  // Front 
  return (
    <div className="main">
      <h1>Robot PP</h1>
      <div class="border d-table w-100">
      </div>
      <div className='container'>
        <div className="history-panel right">
          <div className="history-scroll"  ref={chatHistoryRef}>
            <ul>
            
            {currentChatHistory && currentChatHistory.conversation.map((item, index) => (
              <li className="messages" key={index}>
                {item.responseStudent && (
                  <p className="whatsapp-bubble send">{item.responseStudent}</p>
                )}
                {item.responseChatbot && (
                isImageUrl(item.responseChatbot) ? (
                  <img
                    src={item.responseChatbot}
                    alt="Chatbot Response"
                    className="chatbot-image"
                  />
                ) : (
                  <p className="whatsapp-bubble received">{item.responseChatbot}</p>
                )
              )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
    <div className="search">
      <TextField
        id="outlined-basic"
        value={responseStudent}
        onChange={inputHandler}
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            handleSubmit();
          }
        }}
        variant="outlined" 
        fullWidth
        label="Respuesta"
      />
      <button className="search-button" onClick={handleSubmit} disabled={loading}>
            {loading ? <div className="loading-spinner"></div> : 'Enviar'}
      </button>
      {error && <ErrorModal error={error} onClose={handleClose} />}
    </div>
  </div>
  );
}

export default App;