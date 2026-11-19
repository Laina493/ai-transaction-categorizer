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
    { role: 'bot', text: "Welcome to NamiBooks AI. Enter a transaction manually, or upload a CSV/Excel file to begin." }
  ]);

  // --- MANUAL TRANSACTION (CHAT) ---
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
          const entryWithDate = { ...data.journal_entry, date: new Date().toLocaleDateString('en-GB') };
          setJournalEntries(prev => [...prev, entryWithDate]);
        }
        setMessages(prev => [...prev, { role: 'bot', text: `Categorised as ${data.category}. Ledger updated.` }]);
      } else {
        // SHORTENED MANUAL CHAT MESSAGE
        setMessages(prev => [...prev, { 
          role: 'system', 
          text: `⚠️ I need help with this transaction: "${userText}" (N$${userAmount}). Which category does it belong to?`,
          needsReview: true,
          originalText: userText,
          amount: userAmount,
          date: new Date().toLocaleDateString('en-GB')
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'system', text: "Error: Is the server running?" }]);
    }
    setLoading(false);
  };

  // --- FILE UPLOAD (BATCH) ---
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
      const reviewMessages = [];

      data.results.forEach((item) => {
        if (item.category) {
          // 1. CLEAN UP THE MESSY DESCRIPTION
          let cleanDesc = item.input;
          
          if (cleanDesc.includes('|')) {
            cleanDesc = cleanDesc.split('|')[1];
          }
          
          cleanDesc = cleanDesc.replace(/\([^)]*\)/g, '')
                               .replace(/\s+NA$/i, '')
                               .replace(/\s+/g, ' ')
                               .trim();

          // 2. Push to the middle panel buckets
          const displayStr = `${cleanDesc} (N$${item.amount || 0})`;
          newCats[item.category].push(displayStr);
          
          // 3. Generate the journal entry using the CLEAN description and REAL date
          newEntries.push({
            description: cleanDesc, 
            amount: item.amount || 0,
            date: item.date || new Date().toLocaleDateString('en-GB'), 
            lines: [
              { account: ["Expenses","Assets","Drawings"].includes(item.category) ? item.category : "Bank", debit: item.amount || 0, credit: 0 },
              { account: ["Income","Liabilities","Equity"].includes(item.category) ? item.category : "Bank", debit: 0, credit: item.amount || 0 }
            ]
          });
        } else {
          // 4. SHORTENED BATCH UPLOAD MESSAGE
          reviewMessages.push({
            role: 'system',
            text: `⚠️ I need help with this transaction: "${item.input}" (N$${item.amount}). Which category does it belong to?`,
            needsReview: true,
            originalText: item.input,
            amount: item.amount || 0,
            date: item.date || new Date().toLocaleDateString('en-GB')
          });
        }
      });

      setCategories(newCats);
      setJournalEntries(newEntries);

      // 5. Add the summary and the interactive review prompts to the chat
      setMessages(prev => [
        ...prev, 
        { role: 'bot', text: `Successfully processed ${data.summary.total} transactions. ${data.summary.by_source.needs_review} need your review below.` },
        ...reviewMessages
      ]);

    } catch (error) {
      setMessages(prev => [...prev, { role: 'system', text: "Failed to upload file. Check server." }]);
    }
    setLoading(false);
  };

  // --- HUMAN-IN-THE-LOOP OVERRIDE BUTTONS ---
  const handleManualOverride = (messageIndex, category, originalText) => {
    const messageToResolve = messages[messageIndex];
    
    // 1. Add it to the left panel buckets
    const displayStr = `${originalText} (N$${messageToResolve.amount || 0})`;
    setCategories(prev => ({
      ...prev,
      [category]: [...prev[category], displayStr]
    }));

    // 2. Add it to the General Journal
    setJournalEntries(prev => [...prev, {
      description: originalText,
      amount: messageToResolve.amount || 0,
      date: messageToResolve.date || new Date().toLocaleDateString('en-GB'),
      lines: [
        { account: ["Expenses","Assets","Drawings"].includes(category) ? category : "Bank", debit: messageToResolve.amount || 0, credit: 0 },
        { account: ["Income","Liabilities","Equity"].includes(category) ? category : "Bank", debit: 0, credit: messageToResolve.amount || 0 }
      ]
    }]);

    // 3. Update the chat message so the yellow warning goes away
    setMessages(prev => {
      const newMessages = [...prev];
      newMessages[messageIndex] = {
        role: 'bot',
        text: `Manually categorised "${originalText}" as ${category} (Human-in-the-Loop override) ✅`
      };
      return newMessages;
    });
  };

  // --- DOWNLOAD LEDGER ---
  const downloadLedger = () => {
    if (journalEntries.length === 0) return;
    
    let csvContent = "Date, Description, Account, Debit (N$), Credit (N$)\n";

    journalEntries.forEach(entry => {
      const txDate = entry.date || new Date().toLocaleDateString('en-GB');

      entry.lines.forEach((line, index) => {
        const desc = index === 0 ? `"${entry.description}"` : "";
        const debitVal = line.debit > 0 ? line.debit.toFixed(2) : "0.00";
        const creditVal = line.credit > 0 ? line.credit.toFixed(2) : "0.00";
        
        csvContent += `'${txDate}, ${desc}, ${line.account}, ${debitVal}, ${creditVal}\n`;
      });
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'NamiBooks_General_Ledger.csv';
    a.click();
  };

  const totalDebit = journalEntries.reduce((sum, entry) => sum + entry.lines.reduce((s, l) => s + l.debit, 0), 0);
  const totalCredit = journalEntries.reduce((sum, entry) => sum + entry.lines.reduce((s, l) => s + l.credit, 0), 0);

  return (
    <div className="app-container">
      
      {/* LEFT PANEL */}
      <div className="left-panel">
        <h2>Chat Assistant</h2>
        
        <div className="upload-section">
          <input type="file" accept=".csv, .xlsx" ref={fileInputRef} style={{display: 'none'}} onChange={handleFileUpload} />
          <button className="upload-btn" onClick={() => fileInputRef.current.click()}>
            📄 Upload CSV / Excel
          </button>
        </div>

        <div className="chat-window">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              <div style={{ whiteSpace: 'pre-line' }}>{msg.text}</div>
              
              {/* If this message needs review, show the buttons */}
              {msg.needsReview && (
                <div className="button-group">
                  {Object.keys(categories).map(cat => (
                    <button 
                      key={cat}
                      className={`override-btn btn-${cat.toLowerCase()}`}
                      onClick={() => handleManualOverride(index, cat, msg.originalText)}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          {loading && <div className="message system">Processing...</div>}
        </div>

        <div className="input-area">
          <input 
            type="text" 
            value={input} 
            onChange={(e) => setInput(e.target.value)} 
            placeholder="Describe transaction..." 
            style={{ flex: 3, minWidth: "0" }} 
          />
          <input 
            type="number" 
            value={amount} 
            onChange={(e) => setAmount(e.target.value)} 
            placeholder="N$" 
            style={{ flex: 1, minWidth: "60px" }} 
          />
          <button onClick={handleSend} disabled={loading}>Post</button>
        </div>
      </div>

      {/* MIDDLE PANEL */}
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

      {/* RIGHT PANEL */}
      <div className="right-panel">
        <div className="journal-header">
          <h2>General Journal</h2>
          <button className="download-btn" onClick={downloadLedger} disabled={journalEntries.length === 0}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Download Ledger
          </button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Account</th>
                <th>Debit (N$)</th>
                <th>Credit (N$)</th>
              </tr>
            </thead>
            <tbody>
              {journalEntries.length === 0 ? (
                <tr><td colSpan="5" style={{textAlign: 'center', padding: '20px'}}>No entries yet.</td></tr>
              ) : (
                journalEntries.map((entry, entryIndex) => (
                  <Fragment key={entryIndex}>
                    {entry.lines.map((line, lineIndex) => (
                      <tr key={lineIndex}>
                        <td>{lineIndex === 0 ? entry.date : ''}</td>
                        <td>{lineIndex === 0 ? <strong>{entry.description}</strong> : ''}</td>
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
                <td colSpan="3"><strong>Totals</strong></td>
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