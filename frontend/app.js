// Excel Agent Frontend Application
class ExcelAgent {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.initializeElements();
        this.attachEventListeners();
        this.currentResponse = null;
    }

    initializeElements() {
        this.questionInput = document.getElementById('questionInput');
        this.sendButton = document.getElementById('sendButton');
        this.messages = document.getElementById('messages');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.loadingText = document.getElementById('loadingText');
    }

    attachEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendQuestion());
        this.questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendQuestion();
            }
        });
    }

    async sendQuestion() {
        const question = this.questionInput.value.trim();
        if (!question) return;

        // Add user message to chat
        this.addMessage(question, 'user');

        // Clear input and show loading
        this.questionInput.value = '';
        this.showLoading();

        try {
            const response = await this.callQueryAPI(question);
            this.hideLoading();
            this.showResults(response);
        } catch (error) {
            this.hideLoading();
            this.showError(error.message);
        }
    }

    async callQueryAPI(question) {
        const response = await fetch(`${this.apiBaseUrl}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question }),
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';

        const icon = document.createElement('i');
        icon.className = type === 'user' ? 'fas fa-user' : 'fas fa-robot';
        avatarDiv.appendChild(icon);

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const textP = document.createElement('p');
        textP.textContent = text;
        contentDiv.appendChild(textP);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        this.messages.appendChild(messageDiv);
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    showLoading() {
        this.loadingIndicator.style.display = 'flex';
        this.sendButton.disabled = true;
        this.questionInput.disabled = true;
    }

    hideLoading() {
        this.loadingIndicator.style.display = 'none';
        this.sendButton.disabled = false;
        this.questionInput.disabled = false;
    }

    showError(message) {
        this.addMessage(`Error: ${message}`, 'bot');
    }
}


// Enhanced ExcelAgent with SSE for streaming results
class ExcelAgentWithSSE extends ExcelAgent {
    constructor() {
        super();
        this.currentStreamingMessage = null;
        this.eventSource = null;
        this.activeComponents = {}; // Track active UI components for each content type
    }

    async sendQuestion() {
        const question = this.questionInput.value.trim();
        if (!question) return;

        // Add user message to chat
        this.addMessage(question, 'user');

        // Clear input and show loading
        this.questionInput.value = '';
        this.showLoading();

        try {
            await this.streamQueryResults(question);
        } catch (error) {
            this.hideLoading();
            this.showError(error.message);
        }
    }

    async streamQueryResults(question) {
        return new Promise((resolve, reject) => {
            // Create streaming message for bot response
            this.currentStreamingMessage = this.createStreamingMessage();

            // Connect to SSE endpoint with question as query parameter
            this.eventSource = new EventSource(`${this.apiBaseUrl}/query?question=${encodeURIComponent(question)}`);

            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.code === 0) {
                        this.handleStreamingMessage(data.data);
                        if (data.data.finished === 1) {
                            resolve();
                        }
                    }
                } catch (error) {
                    console.error('Error parsing SSE data:', error);
                    reject(error);
                }
            };

            this.eventSource.onerror = (error) => {
                console.error('SSE Error:', error);
                this.hideLoading();
                this.eventSource.close();
                reject(error);
            };

            this.eventSource.onopen = () => {
                console.log('SSE connection opened');
            };
        });
    }

    createStreamingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message streaming-message';

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';

        const icon = document.createElement('i');
        icon.className = 'fas fa-robot';
        avatarDiv.appendChild(icon);

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content streaming-content';

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        this.messages.appendChild(messageDiv);
        this.messages.scrollTop = this.messages.scrollHeight;

        return contentDiv;
    }

    handleStreamingMessage(data) {
        if (!this.currentStreamingMessage) return;

        const { answer, finished, content_type, content_status } = data;

        // Handle different content types with status lifecycle
        switch (content_type) {
            case 'code':
                this.handleCodeContent(answer, content_status);
                break;
            case 'data':
                this.handleDataContent(answer, content_status);
                break;
            case 'result':
                this.handleResultContent(answer, content_status);
                break;
            case 'error':
                this.handleErrorContent(answer, content_status);
                break;
            default:
                this.handleTextContent(answer, content_status);
        }

        if (finished === 1) {
            this.finishStreaming();
        }
    }

    // Content type handlers with status lifecycle management
    handleCodeContent(answer, status) {
        switch (status) {
            case 'start':
                this.initializeCodeBlock();
                break;
            case 'in_progress':
                this.appendToCodeBlock(answer);
                break;
            case 'end':
                this.finalizeCodeBlock();
                break;
            default:
                this.appendToCodeBlock(answer);
        }
    }

    handleDataContent(answer, status) {
        switch (status) {
            case 'start':
                this.initializeDataTable();
                break;
            case 'in_progress':
                this.appendToDataTable(answer);
                break;
            case 'end':
                this.finalizeDataTable();
                break;
            default:
                this.appendToDataTable(answer);
        }
    }

    handleResultContent(answer, status) {
        switch (status) {
            case 'start':
                this.initializeResultSection();
                break;
            case 'in_progress':
                this.appendToResultSection(answer);
                break;
            case 'end':
                this.finalizeResultSection();
                break;
            default:
                this.appendToResultSection(answer);
        }
    }

    handleErrorContent(answer, status) {
        switch (status) {
            case 'start':
                this.initializeErrorSection();
                break;
            case 'in_progress':
                this.appendToErrorSection(answer);
                break;
            case 'end':
                this.finalizeErrorSection();
                break;
            default:
                this.appendToErrorSection(answer);
        }
    }

    handleTextContent(answer, status) {
        switch (status) {
            case 'start':
                this.initializeTextSection();
                break;
            case 'in_progress':
                this.appendToTextSection(answer);
                break;
            case 'end':
                this.finalizeTextSection();
                break;
            default:
                this.appendToTextSection(answer);
        }
    }

    // Code block lifecycle methods
    initializeCodeBlock() {
        const codeContainer = document.createElement('div');
        codeContainer.className = 'streaming-code-container';
        codeContainer.innerHTML = `
            <div class="content-header">
                <i class="fas fa-code"></i>
                <span>Generated Code</span>
            </div>
            <pre class="streaming-code"><code class="language-python"></code></pre>
        `;
        this.currentStreamingMessage.appendChild(codeContainer);
        this.activeComponents.code = codeContainer.querySelector('code');
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    appendToCodeBlock(code) {
        if (!this.activeComponents.code) {
            this.initializeCodeBlock();
        }
        // Clean code and append
        const cleanCode = code.replace(/```python\n?|\n?```/g, '');
        this.activeComponents.code.textContent += cleanCode;
        Prism.highlightElement(this.activeComponents.code);
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    finalizeCodeBlock() {
        if (this.activeComponents.code) {
            // Add copy button and final styling
            const container = this.activeComponents.code.closest('.streaming-code-container');
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy';
            copyButton.onclick = () => this.copyToClipboard(this.activeComponents.code.textContent);
            container.appendChild(copyButton);
            delete this.activeComponents.code;
        }
    }

    // Data table lifecycle methods
    initializeDataTable() {
        const tableContainer = document.createElement('div');
        tableContainer.className = 'streaming-data-container';
        tableContainer.innerHTML = `
            <div class="content-header">
                <i class="fas fa-table"></i>
                <span>Data Results</span>
            </div>
            <div class="table-wrapper">
                <table class="streaming-table">
                    <thead class="table-header"></thead>
                    <tbody class="table-body"></tbody>
                </table>
            </div>
        `;
        this.currentStreamingMessage.appendChild(tableContainer);
        this.activeComponents.data = {
            container: tableContainer,
            header: tableContainer.querySelector('.table-header'),
            body: tableContainer.querySelector('.table-body'),
            headerInitialized: false
        };
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    appendToDataTable(data) {
        if (!this.activeComponents.data) {
            this.initializeDataTable();
        }

        try {
            // Try to parse data as JSON (assuming it's DataFrame-like structure)
            const parsedData = JSON.parse(data);
            this.renderDataTable(parsedData);
        } catch (e) {
            // If not JSON, treat as raw text
            this.renderDataTableAsText(data);
        }
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    renderDataTable(data) {
        const { header, body, headerInitialized } = this.activeComponents.data;

        if (Array.isArray(data)) {
            // Handle array of objects or arrays
            if (data.length > 0) {
                if (!headerInitialized && typeof data[0] === 'object') {
                    // Initialize header with object keys
                    const headers = Object.keys(data[0]);
                    const headerRow = document.createElement('tr');
                    headers.forEach(headerText => {
                        const th = document.createElement('th');
                        th.textContent = headerText;
                        headerRow.appendChild(th);
                    });
                    header.appendChild(headerRow);
                    this.activeComponents.data.headerInitialized = true;
                }

                // Add data rows
                data.forEach(row => {
                    const tr = document.createElement('tr');
                    if (Array.isArray(row)) {
                        row.forEach(cell => {
                            const td = document.createElement('td');
                            td.textContent = cell || '';
                            tr.appendChild(td);
                        });
                    } else if (typeof row === 'object') {
                        Object.values(row).forEach(cell => {
                            const td = document.createElement('td');
                            td.textContent = cell || '';
                            tr.appendChild(td);
                        });
                    }
                    body.appendChild(tr);
                });
            }
        } else if (typeof data === 'object') {
            // Handle single object
            if (!headerInitialized) {
                const headers = Object.keys(data);
                const headerRow = document.createElement('tr');
                headers.forEach(headerText => {
                    const th = document.createElement('th');
                    th.textContent = headerText;
                    headerRow.appendChild(th);
                });
                header.appendChild(headerRow);
                this.activeComponents.data.headerInitialized = true;
            }

            const tr = document.createElement('tr');
            Object.values(data).forEach(cell => {
                const td = document.createElement('td');
                td.textContent = cell || '';
                tr.appendChild(td);
            });
            body.appendChild(tr);
        }
    }

    renderDataTableAsText(text) {
        // Fallback for non-JSON data - display as formatted text
        const textDiv = document.createElement('div');
        textDiv.className = 'data-text';
        textDiv.innerHTML = this.formatText(text);
        this.activeComponents.data.container.appendChild(textDiv);
    }

    finalizeDataTable() {
        if (this.activeComponents.data) {
            // Add export button and final styling
            const container = this.activeComponents.data.container;
            const exportButton = document.createElement('button');
            exportButton.className = 'export-button';
            exportButton.innerHTML = '<i class="fas fa-download"></i> Export CSV';
            exportButton.onclick = () => this.exportTableToCSV();
            container.appendChild(exportButton);
            delete this.activeComponents.data;
        }
    }

    // Result section lifecycle methods
    initializeResultSection() {
        const resultContainer = document.createElement('div');
        resultContainer.className = 'streaming-result-container';
        resultContainer.innerHTML = `
            <div class="content-header">
                <i class="fas fa-chart-line"></i>
                <span>Analysis Results</span>
            </div>
            <div class="result-content"></div>
        `;
        this.currentStreamingMessage.appendChild(resultContainer);
        this.activeComponents.result = resultContainer.querySelector('.result-content');
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    appendToResultSection(result) {
        if (!this.activeComponents.result) {
            this.initializeResultSection();
        }
        const resultDiv = document.createElement('div');
        resultDiv.className = 'result-text';
        resultDiv.innerHTML = this.formatText(result);
        this.activeComponents.result.appendChild(resultDiv);
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    finalizeResultSection() {
        if (this.activeComponents.result) {
            // Add final styling
            const container = this.activeComponents.result.closest('.streaming-result-container');
            container.classList.add('completed');
            delete this.activeComponents.result;
        }
    }

    // Error section lifecycle methods
    initializeErrorSection() {
        const errorContainer = document.createElement('div');
        errorContainer.className = 'streaming-error-container';
        errorContainer.innerHTML = `
            <div class="content-header error-header">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Error</span>
            </div>
            <div class="error-content"></div>
        `;
        this.currentStreamingMessage.appendChild(errorContainer);
        this.activeComponents.error = errorContainer.querySelector('.error-content');
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    appendToErrorSection(error) {
        if (!this.activeComponents.error) {
            this.initializeErrorSection();
        }
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-text';
        errorDiv.innerHTML = this.formatText(error);
        this.activeComponents.error.appendChild(errorDiv);
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    finalizeErrorSection() {
        if (this.activeComponents.error) {
            delete this.activeComponents.error;
        }
    }

    // Text section lifecycle methods
    initializeTextSection() {
        const textContainer = document.createElement('div');
        textContainer.className = 'streaming-text-container';
        textContainer.innerHTML = '<div class="text-content"></div>';
        this.currentStreamingMessage.appendChild(textContainer);
        this.activeComponents.text = textContainer.querySelector('.text-content');
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    appendToTextSection(text) {
        if (!this.activeComponents.text) {
            this.initializeTextSection();
        }
        const textDiv = document.createElement('div');
        textDiv.className = 'text-segment';
        textDiv.innerHTML = this.formatText(text);
        this.activeComponents.text.appendChild(textDiv);
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    finalizeTextSection() {
        if (this.activeComponents.text) {
            delete this.activeComponents.text;
        }
    }

    // Utility methods
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            // Show temporary success feedback
            const button = event.target;
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            button.classList.add('success');
            setTimeout(() => {
                button.innerHTML = originalText;
                button.classList.remove('success');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy: ', err);
        });
    }

    exportTableToCSV() {
        // Implementation for exporting table data to CSV
        const table = this.activeComponents.data?.container.querySelector('.streaming-table');
        if (!table) return;

        let csv = [];
        const rows = table.querySelectorAll('tr');

        for (let i = 0; i < rows.length; i++) {
            const row = [], cols = rows[i].querySelectorAll('td, th');

            for (let j = 0; j < cols.length; j++) {
                row.push('"' + cols[j].innerText + '"');
            }

            csv.push(row.join(','));
        }

        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');

        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', 'data_export.csv');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    appendText(text) {
        const textDiv = document.createElement('div');
        textDiv.className = 'streaming-text';
        textDiv.innerHTML = this.formatText(text);
        this.currentStreamingMessage.appendChild(textDiv);
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    appendCodeBlock(code) {
        const codeDiv = document.createElement('div');
        codeDiv.className = 'streaming-code';
        codeDiv.innerHTML = `<pre><code class="language-python">${code.replace(/```python\n?|\n?```/g, '')}</code></pre>`;
        this.currentStreamingMessage.appendChild(codeDiv);
        Prism.highlightElement(codeDiv.querySelector('code'));
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    appendResult(result) {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'streaming-result';
        resultDiv.innerHTML = this.formatText(result);
        this.currentStreamingMessage.appendChild(resultDiv);
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    appendError(error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'streaming-error';
        errorDiv.innerHTML = this.formatText(error);
        this.currentStreamingMessage.appendChild(errorDiv);
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    formatText(text) {
        // Basic markdown-like formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
            .replace(/\*(.*?)\*/g, '<em>$1</em>')  // Italic
            .replace(/\n/g, '<br>');  // Line breaks
    }

    finishStreaming() {
        this.hideLoading();
        this.currentStreamingMessage.classList.remove('streaming-message');
        this.currentStreamingMessage = null;
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Use the enhanced version with SSE support
    const app = new ExcelAgentWithSSE();
    console.log('Excel Agent Frontend initialized');
});
