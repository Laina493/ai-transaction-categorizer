import { useState, useRef, Fragment } from 'react';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  const [categories, setCategories] = useState({
    Assets: [], Liabilities: [], Equity: [], Income: [], Expenses: [], Drawings: []
  });

  const [journalEntries, setJournalEntries] = useState([]);
  const [messages, setMessages] = useState([
    { role: 'bot', text: "Welcome! Enter a transaction manually with an amount, or upload a CSV/Excel file to begin." }
  ]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userText = input;
    const userAmount = parseFloat(amount) || 0;
    
    setInput('');
    setAmount('');
    setMessages(prev => [...prev, { role: 'user', text: `${userText} (N$ ${userAmount})` }]);
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: userText, amount: userAmount })
      });
      const data = await response.json();

      if (data.source === 'rule' || data.source === 'ml') {
        setCategories(prev => ({
          ...prev,
          [data.category]: [...prev[data.category], `${userText} (N$${userAmount})`]
        }));
        
        if (data.journal_entry) {
          setJournalEntries(prev => [...prev, data.journal_entry]);
        }
        setMessages(prev => [...prev, { role: 'bot', text: `Categorised as ${data.category}. Ledger updated.` }]);
      } else {
        setMessages(prev => [...prev, { role: 'system', text: `⚠️ ${data.message}` }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'system', text: "Error: Is the server running?" }]);
    }
    setLoading(false);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', text: `Uploaded file: ${file.name}` }]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) throw new Error("Upload failed");
      const data = await response.json();

      const newCats = { ...categories };
      const newEntries = [...journalEntries];

      data.results.forEach(item => {
        if (item.category) {
          const displayStr = `${item.input} (N$${item.amount || 0})`;
          newCats[item.category].push(displayStr);
          
          newEntries.push({
            description: item.input,
            amount: item.amount || 0,
            lines: [
              { account: ["Expenses","Assets","Drawings"].includes(item.category) ? item.category : "Bank", debit: item.amount || 0, credit: 0 },
              { account: ["Income","Liabilities","Equity"].includes(item.category) ? item.category : "Bank", debit: 0, credit: item.amount || 0 }
            ]
          });
        }
      });

      setCategories(newCats);
      setJournalEntries(newEntries);

      setMessages(prev => [...prev, { 
        role: 'bot', 
        text: `Successfully processed ${data.summary.total} transactions. ${data.summary.by_source.needs_review} need review.` 
      }]);

    } catch (error) {
      setMessages(prev => [...prev, { role: 'system', text: "Failed to upload file. Check server." }]);
    }
    setLoading(false);
  };

  const downloadLedger = () => {
    if (journalEntries.length === 0) return;
    let csvContent = "Date,Description,Account,Debit,Credit\n";
    const date = new Date().toLocaleDateString();

    journalEntries.forEach(entry => {
      entry.lines.forEach((line, index) => {
        const desc = index === 0 ? entry.description : "";
        csvContent += `${date},"${desc}",${line.account},${line.debit},${line.credit}\n`;
      });
    });

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'general_ledger.csv';
    a.click();
  };

  const totalDebit = journalEntries.reduce((sum, entry) => sum + entry.lines.reduce((s, l) => s + l.debit, 0), 0);
  const totalCredit = journalEntries.reduce((sum, entry) => sum + entry.lines.reduce((s, l) => s + l.credit, 0), 0);

  return (
    <div className="app-container">
      
      <div className="left-panel">
        <h2>AI Assistant</h2>
        
        <div className="upload-section">
          <input type="file" accept=".csv, .xlsx" ref={fileInputRef} style={{display: 'none'}} onChange={handleFileUpload} />
          <button className="upload-btn" onClick={() => fileInputRef.current.click()}>
            📄 Upload CSV / Excel
          </button>
        </div>

        <div className="chat-window">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>{msg.text}</div>
          ))}
          {loading && <div className="message system">Processing...</div>}
        </div>

        <div className="input-area">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Transaction..." style={{ flex: 2 }} />
          <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="N$" style={{ flex: 1 }} />
          <button onClick={handleSend} disabled={loading}>Post</button>
        </div>
      </div>

      <div className="middle-panel">
        <h2>Categories</h2>
        <div className="buckets">
          {Object.entries(categories).map(([cat, items]) => (
            <div key={cat} className="bucket">
              <div className="bucket-title">{cat} ({items.length})</div>
              <ul className="bucket-list">
                {items.map((item, i) => <li key={i}>{item}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="right-panel">
        <div className="journal-header">
          <h2>General Journal</h2>
          <button className="download-btn" onClick={downloadLedger} disabled={journalEntries.length === 0}>
            ⬇️ Download Ledger
          </button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr><th>Account</th><th>Debit (N$)</th><th>Credit (N$)</th></tr>
            </thead>
            <tbody>
              {journalEntries.length === 0 ? (
                <tr><td colSpan="3" style={{textAlign: 'center', padding: '20px'}}>No entries yet.</td></tr>
              ) : (
                journalEntries.map((entry, entryIndex) => (
                  <Fragment key={entryIndex}>
                    <tr className="journal-description-row">
                      <td colSpan="3"><strong>{entry.description}</strong></td>
                    </tr>
                    {entry.lines.map((line, lineIndex) => (
                      <tr key={lineIndex}>
                        <td>{line.account}</td>
                        <td>{line.debit > 0 ? line.debit.toFixed(2) : ''}</td>
                        <td>{line.credit > 0 ? line.credit.toFixed(2) : ''}</td>
                      </tr>
                    ))}
                  </Fragment>
                ))
              )}
            </tbody>
            <tfoot>
              <tr className="totals-row">
                <td><strong>Totals</strong></td>
                <td><strong>N$ {totalDebit.toFixed(2)}</strong></td>
                <td><strong>N$ {totalCredit.toFixed(2)}</strong></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

    </div>
  );
}

export default App;