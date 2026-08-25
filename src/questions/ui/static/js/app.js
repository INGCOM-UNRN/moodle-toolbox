// mxviz - Client-side Application

class MxvizApp {
    constructor() {
        this.currentQuestion = null;
        this.currentFilepath = null;
        this.allQuestions = []; // Lista lineal de todas las preguntas
        this.currentIndex = -1; // Índice actual en la lista
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupResizer();
        await this.loadTree();
    }

    setupEventListeners() {
        // Search
        document.getElementById('search-btn').addEventListener('click', () => this.handleSearch());
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSearch();
        });

        // Sidebar toggle
        document.getElementById('toggle-sidebar-btn').addEventListener('click', () => this.toggleSidebar());
        document.getElementById('floating-sidebar-toggle').addEventListener('click', () => this.toggleSidebar());

        // Navigation buttons
        document.getElementById('first-btn').addEventListener('click', () => this.navigateToFirst());
        document.getElementById('prev-btn').addEventListener('click', () => this.navigateToPrevious());
        document.getElementById('next-btn').addEventListener('click', () => this.navigateToNext());
        document.getElementById('last-btn').addEventListener('click', () => this.navigateToLast());

        // Editor actions
        document.getElementById('save-btn').addEventListener('click', () => this.saveQuestion());
        document.getElementById('cancel-btn').addEventListener('click', () => this.cancelEdit());

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Tags input
        document.getElementById('tags-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addTag(e.target.value);
                e.target.value = '';
            }
        });

        // Add answer button
        document.getElementById('add-answer-btn').addEventListener('click', () => this.addAnswer());

        // Question text change for preview
        document.getElementById('question-text').addEventListener('input', () => {
            this.updatePreview();
        });

        // Fullwidth character conversion buttons
        document.getElementById('apply-fullwidth-btn').addEventListener('click', () => this.applyFullwidthConversion());
        document.getElementById('undo-fullwidth-btn').addEventListener('click', () => this.undoFullwidthConversion());
    }

    async loadTree() {
        const loading = document.getElementById('loading');
        const treeContainer = document.getElementById('tree-container');

        try {
            const response = await fetch('/api/tree');
            const data = await response.json();

            loading.style.display = 'none';
            this.renderTree(data, treeContainer);
            
            // Construir lista lineal de preguntas para navegación
            this.allQuestions = this.buildQuestionsList(data);
            console.log(`Total de preguntas cargadas: ${this.allQuestions.length}`);
        } catch (error) {
            loading.textContent = 'Error cargando árbol: ' + error.message;
        }
    }

    renderTree(items, container) {
        items.forEach(item => {
            const node = document.createElement('div');
            node.className = 'tree-node';

            if (item.type === 'directory') {
                const dirItem = document.createElement('div');
                dirItem.className = 'tree-item';
                
                const hasChildren = item.children && item.children.length > 0;
                
                dirItem.innerHTML = `
                    <span class="icon">📁</span>
                    <span class="name">${item.name}</span>
                    <span class="count">${item.question_count}</span>
                `;
                node.appendChild(dirItem);

                if (hasChildren) {
                    const children = document.createElement('div');
                    children.className = 'tree-children';
                    this.renderTree(item.children, children);
                    node.appendChild(children);
                }
            } else if (item.type === 'file') {
                const fileItem = document.createElement('div');
                fileItem.className = 'tree-item';
                fileItem.innerHTML = `
                    <span class="icon">${this.getTypeIcon(item.question_type)}</span>
                    <span class="name">${item.question_name || item.name}</span>
                `;
                fileItem.addEventListener('click', () => this.loadQuestion(item.path));
                node.appendChild(fileItem);
            }

            container.appendChild(node);
        });
    }

    getTypeIcon(type) {
        const icons = {
            'multichoice': '✅',
            'truefalse': '✔️',
            'shortanswer': '✏️',
            'numerical': '🔢',
            'essay': '📝',
            'matching': '🔗',
            'unknown': '❓'
        };
        return icons[type] || icons['unknown'];
    }

    async loadQuestion(filepath) {
        try {
            this.showStatus('Cargando pregunta...');
            const response = await fetch(`/api/question/${filepath}`);
            const question = await response.json();

            if (question.error) {
                this.showStatus('Error: ' + question.error, 'error');
                return;
            }

            this.currentQuestion = question;
            this.currentFilepath = filepath;
            
            // Actualizar índice actual en la lista de navegación
            this.currentIndex = this.allQuestions.findIndex(q => q.path === filepath);
            
            this.renderQuestion(question);
            this.showEditor();
            this.showStatus('Pregunta cargada');
            this.updateNavigationBar();

            // Highlight active item
            document.querySelectorAll('.tree-item').forEach(item => {
                item.classList.remove('active');
            });
        } catch (error) {
            this.showStatus('Error cargando pregunta: ' + error.message, 'error');
        }
    }

    renderQuestion(question) {
        // Header
        document.getElementById('question-type').textContent = question.type;
        document.getElementById('question-name').value = question.name || '';

        // Content
        document.getElementById('question-text').value = question.questiontext || '';
        document.getElementById('general-feedback').value = question.generalfeedback || '';
        document.getElementById('default-grade').value = question.defaultgrade || '1';
        document.getElementById('penalty').value = question.penalty || '0.1';
        
        // Actualizar selector de formato (si existe)
        const textFormatElem = document.getElementById('questiontext-format');
        if (textFormatElem) {
            textFormatElem.value = question.questiontext_format || 'html';
        }

        // Answers
        const answersContainer = document.getElementById('answers-container');
        answersContainer.innerHTML = '';
        if (question.answers && question.answers.length > 0) {
            question.answers.forEach((answer, index) => {
                this.renderAnswer(answer, index);
            });
        }

        // Tags
        this.renderTags(question.tags || []);

        // Type-specific options
        this.renderTypeSpecificOptions(question);

        // File path
        document.getElementById('file-path').textContent = this.currentFilepath;

        // Update preview
        this.updatePreview();
    }

    renderAnswer(answer, index) {
        const answersContainer = document.getElementById('answers-container');
        const answerDiv = document.createElement('div');
        answerDiv.className = 'answer-item';
        answerDiv.dataset.index = index;

        answerDiv.innerHTML = `
            <div class="answer-header">
                <label>Puntos:</label>
                <input type="number" class="answer-fraction" value="${answer.fraction}" step="1" min="0" max="100"/>
                <button class="answer-delete" onclick="app.removeAnswer(${index})">🗑️ Eliminar</button>
            </div>
            <textarea class="answer-text" rows="2" placeholder="Texto de la respuesta">${answer.text || ''}</textarea>
            <textarea class="answer-feedback" rows="2" placeholder="Retroalimentación (opcional)">${answer.feedback || ''}</textarea>
        `;

        answersContainer.appendChild(answerDiv);
    }

    renderTags(tags) {
        const tagsContainer = document.getElementById('tags-container');
        tagsContainer.innerHTML = '';

        tags.forEach(tag => {
            const tagElem = document.createElement('span');
            tagElem.className = 'tag';
            tagElem.innerHTML = `
                ${tag}
                <button class="tag-remove" onclick="app.removeTag('${tag}')">×</button>
            `;
            tagsContainer.appendChild(tagElem);
        });
    }

    renderTypeSpecificOptions(question) {
        const container = document.getElementById('type-specific-options');
        container.innerHTML = '';

        if (question.type === 'multichoice') {
            container.innerHTML = `
                <div class="form-group">
                    <label for="single">Respuesta única:</label>
                    <select id="single">
                        <option value="1" ${question.single === '1' ? 'selected' : ''}>Sí</option>
                        <option value="0" ${question.single === '0' ? 'selected' : ''}>No (múltiples respuestas)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="shuffleanswers">Mezclar respuestas:</label>
                    <select id="shuffleanswers">
                        <option value="1" ${question.shuffleanswers === '1' ? 'selected' : ''}>Sí</option>
                        <option value="0" ${question.shuffleanswers === '0' ? 'selected' : ''}>No</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="answernumbering">Numeración:</label>
                    <select id="answernumbering">
                        <option value="abc" ${question.answernumbering === 'abc' ? 'selected' : ''}>a, b, c, ...</option>
                        <option value="ABCD" ${question.answernumbering === 'ABCD' ? 'selected' : ''}>A, B, C, ...</option>
                        <option value="123" ${question.answernumbering === '123' ? 'selected' : ''}>1, 2, 3, ...</option>
                        <option value="none" ${question.answernumbering === 'none' ? 'selected' : ''}>Sin numeración</option>
                    </select>
                </div>
            `;
        } else if (question.type === 'shortanswer') {
            container.innerHTML = `
                <div class="form-group">
                    <label for="usecase">Sensible a mayúsculas:</label>
                    <select id="usecase">
                        <option value="0" ${question.usecase === '0' ? 'selected' : ''}>No</option>
                        <option value="1" ${question.usecase === '1' ? 'selected' : ''}>Sí</option>
                    </select>
                </div>
            `;
        } else if (question.type === 'essay') {
            container.innerHTML = `
                <div class="form-group">
                    <label for="responseformat">Formato de respuesta:</label>
                    <select id="responseformat">
                        <option value="editor" ${question.responseformat === 'editor' ? 'selected' : ''}>Editor HTML</option>
                        <option value="editorfilepicker" ${question.responseformat === 'editorfilepicker' ? 'selected' : ''}>Editor + archivos</option>
                        <option value="plain" ${question.responseformat === 'plain' ? 'selected' : ''}>Texto plano</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="responsefieldlines">Líneas de respuesta:</label>
                    <input type="number" id="responsefieldlines" value="${question.responsefieldlines || '15'}" min="1"/>
                </div>
            `;
        }
    }

    addAnswer() {
        const newAnswer = {
            fraction: '0',
            text: '',
            feedback: '',
            format: 'html'
        };
        const index = document.querySelectorAll('.answer-item').length;
        this.renderAnswer(newAnswer, index);
    }

    removeAnswer(index) {
        const answerItem = document.querySelector(`.answer-item[data-index="${index}"]`);
        if (answerItem) {
            answerItem.remove();
        }
    }

    addTag(tagText) {
        if (!tagText.trim()) return;

        const tagsContainer = document.getElementById('tags-container');
        const tagElem = document.createElement('span');
        tagElem.className = 'tag';
        tagElem.innerHTML = `
            ${tagText}
            <button class="tag-remove" onclick="app.removeTag('${tagText}')">×</button>
        `;
        tagsContainer.appendChild(tagElem);
    }

    removeTag(tagText) {
        const tags = document.querySelectorAll('.tag');
        tags.forEach(tag => {
            if (tag.textContent.trim().startsWith(tagText)) {
                tag.remove();
            }
        });
    }

    switchTab(tabName) {
        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = 'none';
        });

        if (tabName === 'edit') {
            document.getElementById('edit-tab').style.display = 'block';
            // Show edit elements, hide preview elements
            document.querySelectorAll('.edit-only').forEach(el => el.style.display = '');
            document.querySelectorAll('.preview-only').forEach(el => el.style.display = 'none');
        } else if (tabName === 'preview') {
            document.getElementById('preview-tab').style.display = 'block';
            // Hide edit elements, show preview elements
            document.querySelectorAll('.edit-only').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.preview-only').forEach(el => el.style.display = 'block');
            this.updateFullPreview();
        }
    }

    updatePreview() {
        const questionText = document.getElementById('question-text').value;
        const previewBox = document.getElementById('question-preview');
        previewBox.innerHTML = this.renderMarkdown(questionText);
    }
    
    updateFullPreview() {
        // Update question text preview
        this.updatePreview();
        
        // Update general feedback preview
        const generalFeedback = document.getElementById('general-feedback').value;
        const feedbackPreview = document.getElementById('general-feedback-preview');
        feedbackPreview.innerHTML = this.renderMarkdown(generalFeedback) || '<em style="color: #999;">Sin retroalimentación general</em>';
        
        // Update answers preview
        this.updateAnswersPreview();
        
        // Update options preview
        const defaultGrade = document.getElementById('default-grade').value;
        const penalty = document.getElementById('penalty').value;
        document.getElementById('default-grade-preview').textContent = defaultGrade || '1';
        document.getElementById('penalty-preview').textContent = penalty || '0.1';
        
        // Update type-specific options preview
        this.updateTypeSpecificPreview();
        
        // Update tags preview
        this.updateTagsPreview();
    }
    
    updateAnswersPreview() {
        const answersPreview = document.getElementById('answers-preview-container');
        answersPreview.innerHTML = '';
        
        const answerItems = document.querySelectorAll('.answer-item');
        if (answerItems.length === 0) {
            answersPreview.innerHTML = '<p style="color: #999; font-style: italic;">No hay respuestas definidas</p>';
            return;
        }
        
        answerItems.forEach((answerDiv, index) => {
            const fraction = parseFloat(answerDiv.querySelector('.answer-fraction').value) || 0;
            const text = answerDiv.querySelector('.answer-text').value;
            const feedback = answerDiv.querySelector('.answer-feedback').value;
            
            const answerPreview = document.createElement('div');
            answerPreview.className = 'answer-preview-item';
            
            // Determine class based on fraction
            if (fraction >= 100) {
                answerPreview.classList.add('correct');
            } else if (fraction > 0) {
                answerPreview.classList.add('partial');
            } else {
                answerPreview.classList.add('incorrect');
            }
            
            // Radio button or checkbox based on question type
            const inputType = this.currentQuestion && this.currentQuestion.single === '0' ? 'checkbox' : 'radio';
            
            answerPreview.innerHTML = `
                <input type="${inputType}" name="answer_preview" class="answer-preview-radio" disabled>
                <div class="answer-preview-content">
                    <div class="answer-preview-text">${this.renderMarkdown(text) || '<em style="color: #999;">Respuesta vacía</em>'}</div>
                    ${fraction > 0 ? `<div class="answer-preview-points">${fraction}% de los puntos</div>` : ''}
                    ${feedback ? `<div class="answer-preview-feedback">${this.renderMarkdown(feedback)}</div>` : ''}
                </div>
            `;
            
            answersPreview.appendChild(answerPreview);
        });
    }
    
    updateTypeSpecificPreview() {
        const container = document.getElementById('type-specific-options-preview');
        container.innerHTML = '';
        
        if (!this.currentQuestion) return;
        
        if (this.currentQuestion.type === 'multichoice') {
            const single = document.getElementById('single')?.value;
            const shuffle = document.getElementById('shuffleanswers')?.value;
            const numbering = document.getElementById('answernumbering')?.value;
            
            container.innerHTML = `
                <div class="preview-item">
                    <span class="preview-label">Tipo de respuesta:</span>
                    <span class="preview-value">${single === '1' ? 'Respuesta única' : 'Múltiples respuestas'}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Mezclar respuestas:</span>
                    <span class="preview-value">${shuffle === '1' ? 'Sí' : 'No'}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Numeración:</span>
                    <span class="preview-value">${this.getNumberingLabel(numbering)}</span>
                </div>
            `;
        } else if (this.currentQuestion.type === 'shortanswer') {
            const usecase = document.getElementById('usecase')?.value;
            container.innerHTML = `
                <div class="preview-item">
                    <span class="preview-label">Sensible a mayúsculas:</span>
                    <span class="preview-value">${usecase === '1' ? 'Sí' : 'No'}</span>
                </div>
            `;
        } else if (this.currentQuestion.type === 'essay') {
            const format = document.getElementById('responseformat')?.value;
            const lines = document.getElementById('responsefieldlines')?.value;
            
            container.innerHTML = `
                <div class="preview-item">
                    <span class="preview-label">Formato de respuesta:</span>
                    <span class="preview-value">${this.getResponseFormatLabel(format)}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Líneas de respuesta:</span>
                    <span class="preview-value">${lines || '15'}</span>
                </div>
            `;
        }
    }
    
    updateTagsPreview() {
        const tagsPreview = document.getElementById('tags-preview-container');
        const tags = this.collectTags();
        
        tagsPreview.innerHTML = '';
        
        if (tags.length === 0) {
            tagsPreview.innerHTML = '<em style="color: #999;">Sin tags</em>';
            return;
        }
        
        tags.forEach(tag => {
            const tagElem = document.createElement('span');
            tagElem.className = 'tag';
            tagElem.textContent = tag;
            tagsPreview.appendChild(tagElem);
        });
    }
    
    getNumberingLabel(value) {
        const labels = {
            'abc': 'a, b, c, ...',
            'ABCD': 'A, B, C, ...',
            '123': '1, 2, 3, ...',
            'none': 'Sin numeración'
        };
        return labels[value] || value;
    }
    
    getResponseFormatLabel(value) {
        const labels = {
            'editor': 'Editor HTML',
            'editorfilepicker': 'Editor + archivos',
            'plain': 'Texto plano'
        };
        return labels[value] || value;
    }
    
    renderMarkdown(text) {
        if (!text) return '';
        
        // Usar marked.js si está disponible, sino fallback a renderizado básico
        if (typeof marked !== 'undefined') {
            try {
                // Configurar marked para renderizado seguro
                marked.setOptions({
                    breaks: true,        // Convertir \n en <br>
                    gfm: true,           // GitHub Flavored Markdown
                    headerIds: false,    // No generar IDs en headers
                    mangle: false        // No codificar emails
                });
                
                return marked.parse(text);
            } catch (e) {
                console.error('Error renderizando Markdown:', e);
                return this.renderMarkdownBasic(text);
            }
        }
        
        return this.renderMarkdownBasic(text);
    }
    
    renderMarkdownBasic(text) {
        // Fallback: renderizado básico si marked.js no está disponible
        let html = text
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/`(.+?)`/g, '<code>$1</code>')
            .replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>')
            .replace(/\n/g, '<br>');

        return html;
    }

    async saveQuestion() {
        try {
            this.showStatus('Guardando...', 'info');

            // Obtener formato de texto seleccionado (si existe el selector)
            const textFormatElem = document.getElementById('questiontext-format');
            const textFormat = textFormatElem ? textFormatElem.value : (this.currentQuestion.questiontext_format || 'html');

            // Recopilar datos del formulario
            const questionData = {
                type: this.currentQuestion.type,
                name: document.getElementById('question-name').value,
                questiontext: document.getElementById('question-text').value,
                questiontext_format: textFormat,
                generalfeedback: document.getElementById('general-feedback').value,
                defaultgrade: document.getElementById('default-grade').value,
                penalty: document.getElementById('penalty').value,
                answers: this.collectAnswers(),
                tags: this.collectTags(),
            };

            // Agregar opciones específicas por tipo
            if (this.currentQuestion.type === 'multichoice') {
                const singleElem = document.getElementById('single');
                const shuffleElem = document.getElementById('shuffleanswers');
                const numberingElem = document.getElementById('answernumbering');
                
                if (singleElem) questionData.single = singleElem.value;
                if (shuffleElem) questionData.shuffleanswers = shuffleElem.value;
                if (numberingElem) questionData.answernumbering = numberingElem.value;
            } else if (this.currentQuestion.type === 'shortanswer') {
                const usecaseElem = document.getElementById('usecase');
                if (usecaseElem) questionData.usecase = usecaseElem.value;
            } else if (this.currentQuestion.type === 'essay') {
                const formatElem = document.getElementById('responseformat');
                const linesElem = document.getElementById('responsefieldlines');
                
                if (formatElem) questionData.responseformat = formatElem.value;
                if (linesElem) questionData.responsefieldlines = linesElem.value;
            }

            // Enviar al servidor
            const response = await fetch(`/api/question/${this.currentFilepath}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(questionData)
            });

            const result = await response.json();

            if (result.error) {
                this.showStatus('Error: ' + result.error, 'error');
            } else {
                this.showStatus('✅ Guardado exitosamente', 'success');
            }
        } catch (error) {
            this.showStatus('Error guardando: ' + error.message, 'error');
        }
    }

    collectAnswers() {
        const answers = [];
        document.querySelectorAll('.answer-item').forEach(answerDiv => {
            const fraction = answerDiv.querySelector('.answer-fraction').value;
            const text = answerDiv.querySelector('.answer-text').value;
            const feedback = answerDiv.querySelector('.answer-feedback').value;

            answers.push({
                fraction: fraction,
                text: text,
                feedback: feedback,
                format: 'html'
            });
        });
        return answers;
    }

    collectTags() {
        const tags = [];
        document.querySelectorAll('.tag').forEach(tagElem => {
            const tagText = tagElem.textContent.trim().replace('×', '').trim();
            if (tagText) tags.push(tagText);
        });
        return tags;
    }

    cancelEdit() {
        if (confirm('¿Descartar cambios?')) {
            if (this.currentFilepath) {
                this.loadQuestion(this.currentFilepath);
            } else {
                this.showWelcome();
            }
        }
    }

    async handleSearch() {
        const query = document.getElementById('search-input').value;
        if (!query.trim()) return;

        try {
            this.showStatus('Buscando...', 'info');
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();

            this.showSearchResults(results, query);
            this.showStatus(`Encontrados ${results.length} resultados`);
        } catch (error) {
            this.showStatus('Error en búsqueda: ' + error.message, 'error');
        }
    }

    showSearchResults(results, query) {
        const resultsDiv = document.getElementById('search-results');
        const resultsContainer = document.getElementById('results-container');
        const welcomeDiv = document.getElementById('welcome');
        const editorDiv = document.getElementById('editor');

        // Ocultar otras vistas
        welcomeDiv.style.display = 'none';
        editorDiv.style.display = 'none';
        resultsDiv.style.display = 'block';

        // Limpiar resultados anteriores
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>No se encontraron resultados.</p>';
            return;
        }

        results.forEach(result => {
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result-item';
            resultDiv.innerHTML = `
                <div class="result-name">${this.highlightQuery(result.name, query)}</div>
                <div class="result-category">📁 ${result.category} | ${this.getTypeIcon(result.type)} ${result.type}</div>
                <div class="result-preview">${this.highlightQuery(result.preview, query)}</div>
            `;
            resultDiv.addEventListener('click', () => {
                this.loadQuestion(result.path);
            });
            resultsContainer.appendChild(resultDiv);
        });
    }

    highlightQuery(text, query) {
        if (!text || !query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    showEditor() {
        document.getElementById('welcome').style.display = 'none';
        document.getElementById('search-results').style.display = 'none';
        document.getElementById('editor').style.display = 'block';
        document.getElementById('navigation-bar').style.display = 'flex';
    }

    showWelcome() {
        document.getElementById('editor').style.display = 'none';
        document.getElementById('search-results').style.display = 'none';
        document.getElementById('welcome').style.display = 'block';
        document.getElementById('navigation-bar').style.display = 'none';
    }

    showStatus(message, type = 'info') {
        const statusMessage = document.getElementById('status-message');
        statusMessage.textContent = message;
        statusMessage.style.color = type === 'error' ? 'var(--danger-color)' : 
                                   type === 'success' ? 'var(--secondary-color)' : 
                                   'var(--text-muted)';
    }

    // Navigation methods
    buildQuestionsList(items, list = []) {
        items.forEach(item => {
            if (item.type === 'file') {
                list.push({
                    name: item.name,
                    path: item.path
                });
            } else if (item.type === 'directory' && item.children) {
                this.buildQuestionsList(item.children, list);
            }
        });
        return list;
    }

    updateNavigationBar() {
        if (this.allQuestions.length === 0) return;

        const counter = document.getElementById('question-counter');
        const navName = document.getElementById('nav-question-name');
        const firstBtn = document.getElementById('first-btn');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const lastBtn = document.getElementById('last-btn');

        counter.textContent = `${this.currentIndex + 1} / ${this.allQuestions.length}`;
        
        if (this.currentIndex >= 0 && this.currentIndex < this.allQuestions.length) {
            navName.textContent = this.allQuestions[this.currentIndex].name;
        }

        // Habilitar/deshabilitar botones según posición
        firstBtn.disabled = this.currentIndex <= 0;
        prevBtn.disabled = this.currentIndex <= 0;
        nextBtn.disabled = this.currentIndex >= this.allQuestions.length - 1;
        lastBtn.disabled = this.currentIndex >= this.allQuestions.length - 1;
    }

    navigateToFirst() {
        if (this.allQuestions.length > 0) {
            this.navigateToIndex(0);
        }
    }

    navigateToPrevious() {
        if (this.currentIndex > 0) {
            this.navigateToIndex(this.currentIndex - 1);
        }
    }

    navigateToNext() {
        if (this.currentIndex < this.allQuestions.length - 1) {
            this.navigateToIndex(this.currentIndex + 1);
        }
    }

    navigateToLast() {
        if (this.allQuestions.length > 0) {
            this.navigateToIndex(this.allQuestions.length - 1);
        }
    }

    navigateToIndex(index) {
        if (index >= 0 && index < this.allQuestions.length) {
            const question = this.allQuestions[index];
            this.loadQuestion(question.path);
        }
    }

    // Fullwidth character conversion
    applyFullwidthConversion() {
        const textarea = document.getElementById('question-text');
        const text = textarea.value;
        
        // Diccionario de sustituciones: normal -> fullwidth
        const substitutions = {
            "==": "⩵",
            "=": "＝",
            ";": ";",
            "#": "＃",
            "{": "｛",
            "}": "｝",
            " ": " ",
            ">": "＞",
            "<": "＜",
            "[": "［",
            "]": "］",
            "(": "（",
            ")": "）",
            "*": "＊",
            '"': "＂",
            ":": "："
        };
        
        let converted = text;
        
        // PROTEGER guardas CDATA - guardar las guardas completas sin modificar
        const cdataStartPattern = /<!\[CDATA\[/g;
        const cdataEndPattern = /\]\]>/g;
        const cdataStarts = [];
        const cdataEnds = [];
        
        // Reemplazar guardas de inicio con placeholders
        converted = converted.replace(cdataStartPattern, (match) => {
            const placeholder = `__CDATA_START_${cdataStarts.length}__`;
            cdataStarts.push(match);
            return placeholder;
        });
        
        // Reemplazar guardas de cierre con placeholders
        converted = converted.replace(cdataEndPattern, (match) => {
            const placeholder = `__CDATA_END_${cdataEnds.length}__`;
            cdataEnds.push(match);
            return placeholder;
        });
        
        // PROTEGER sintaxis Markdown
        // IMPORTANTE: El orden importa - de más específico a más general
        const markdownBlocks = [];
        let mdIndex = 0;
        
        // 1. Proteger bloques de código primero (más específico)
        converted = converted.replace(/(```[\s\S]*?```)/g, (match) => {
            const placeholder = `__MD_CODE_BLOCK_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // 2. Proteger código inline
        converted = converted.replace(/(`[^`\n]+`)/g, (match) => {
            const placeholder = `__MD_INLINE_CODE_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // 3. Proteger blockquotes (líneas completas que empiezan con >)
        converted = converted.replace(/^(>\s+.*)$/gm, (match) => {
            const placeholder = `__MD_BLOCKQUOTE_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // 4. Proteger headers (# al inicio de línea)
        converted = converted.replace(/^(#{1,6}\s+.*)$/gm, (match) => {
            const placeholder = `__MD_HEADER_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // 5. Proteger listas (*, - al inicio de línea)
        converted = converted.replace(/^(\s*[*\-]\s+.*)$/gm, (match) => {
            const placeholder = `__MD_LIST_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // 6. Proteger negrita/cursiva (**texto** o *texto*)
        converted = converted.replace(/(\*{1,2}[^\*\n]+?\*{1,2})/g, (match) => {
            const placeholder = `__MD_EMPHASIS_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // Aplicar sustituciones
        // Primero aplicar == para que no se confunda con =
        if (substitutions["=="]) {
            converted = converted.replace(/==/g, substitutions["=="]);
        }
        
        // Luego aplicar el resto de sustituciones
        for (const [normal, fullwidth] of Object.entries(substitutions)) {
            if (normal !== "==") {
                // Escapar caracteres especiales para regex
                const escapedNormal = normal.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const regex = new RegExp(escapedNormal, 'g');
                converted = converted.replace(regex, fullwidth);
            }
        }
        
        // Restaurar bloques Markdown sin modificar
        markdownBlocks.forEach(({ placeholder, original }) => {
            converted = converted.replace(placeholder, original);
        });
        
        // Agregar ↵ al final de cada línea para hacer explícitos los saltos de línea
        converted = converted.replace(/\n/g, '↵\n');
        
        // Restaurar guardas CDATA sin modificar
        cdataStarts.forEach((guard, index) => {
            const placeholder = `__CDATA_START_${index}__`;
            converted = converted.replace(placeholder, guard);
        });
        
        cdataEnds.forEach((guard, index) => {
            const placeholder = `__CDATA_END_${index}__`;
            converted = converted.replace(placeholder, guard);
        });
        
        textarea.value = converted;
        this.updatePreview();
        this.showNotification('Conversión a fullwidth aplicada (saltos de línea marcados con ↵)', 'success');
    }

    undoFullwidthConversion() {
        const textarea = document.getElementById('question-text');
        const text = textarea.value;
        
        // Diccionario de sustituciones: fullwidth -> normal
        const reverseSubstitutions = {
            "⩵": "==",
            "＝": "=",
            ";": ";",
            "＃": "#",
            "｛": "{",
            "｝": "}",
            " ": " ",
            "＞": ">",
            "＜": "<",
            "［": "[",
            "］": "]",
            "（": "(",
            "）": ")",
            "＊": "*",
            "＂": '"',
            "：": ":",
            "↵": ""  // Eliminar marcadores de salto de línea
        };
        
        let converted = text;
        
        // PROTEGER guardas CDATA antes de revertir
        const cdataStartPattern = /<!\[CDATA\[/g;
        const cdataEndPattern = /\]\]>/g;
        const cdataStarts = [];
        const cdataEnds = [];
        
        // Reemplazar guardas de inicio con placeholders
        converted = converted.replace(cdataStartPattern, (match) => {
            const placeholder = `__CDATA_START_${cdataStarts.length}__`;
            cdataStarts.push(match);
            return placeholder;
        });
        
        // Reemplazar guardas de cierre con placeholders
        converted = converted.replace(cdataEndPattern, (match) => {
            const placeholder = `__CDATA_END_${cdataEnds.length}__`;
            cdataEnds.push(match);
            return placeholder;
        });
        
        // PROTEGER sintaxis Markdown (mismo orden que en apply)
        const markdownBlocks = [];
        let mdIndex = 0;
        
        // 1. Proteger bloques de código primero
        converted = converted.replace(/(```[\s\S]*?```)/g, (match) => {
            const placeholder = `__MD_CODE_BLOCK_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // 2. Proteger código inline
        converted = converted.replace(/(`[^`\n]+`)/g, (match) => {
            const placeholder = `__MD_INLINE_CODE_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // 3. Proteger blockquotes
        converted = converted.replace(/^(>\s+.*)$/gm, (match) => {
            const placeholder = `__MD_BLOCKQUOTE_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // 4. Proteger headers
        converted = converted.replace(/^(#{1,6}\s+.*)$/gm, (match) => {
            const placeholder = `__MD_HEADER_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // 5. Proteger listas
        converted = converted.replace(/^(\s*[*\-]\s+.*)$/gm, (match) => {
            const placeholder = `__MD_LIST_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // 6. Proteger negrita/cursiva
        converted = converted.replace(/(\*{1,2}[^\*\n]+?\*{1,2})/g, (match) => {
            const placeholder = `__MD_EMPHASIS_${mdIndex++}__`;
            markdownBlocks.push({ placeholder, original: match });
            return placeholder;
        });
        
        // Aplicar sustituciones reversas
        for (const [fullwidth, normal] of Object.entries(reverseSubstitutions)) {
            // Escapar caracteres especiales en fullwidth para regex
            const escapedFullwidth = fullwidth.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp(escapedFullwidth, 'g');
            converted = converted.replace(regex, normal);
        }
        
        // Restaurar bloques Markdown sin modificar
        markdownBlocks.forEach(({ placeholder, original }) => {
            converted = converted.replace(placeholder, original);
        });
        
        // Restaurar guardas CDATA sin modificar
        cdataStarts.forEach((guard, index) => {
            const placeholder = `__CDATA_START_${index}__`;
            converted = converted.replace(placeholder, guard);
        });
        
        cdataEnds.forEach((guard, index) => {
            const placeholder = `__CDATA_END_${index}__`;
            converted = converted.replace(placeholder, guard);
        });
        
        textarea.value = converted;
        this.updatePreview();
        this.showNotification('Conversión fullwidth revertida', 'success');
    }

    showNotification(message, type = 'info') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // Remover después de 3 segundos
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Resizer functionality
    setupResizer() {
        const resizer = document.getElementById('resizer');
        const sidebar = document.getElementById('sidebar');
        const editorArea = document.getElementById('editor-area');
        
        let isResizing = false;
        let startX = 0;
        let startWidth = 0;

        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startWidth = sidebar.offsetWidth;
            resizer.classList.add('resizing');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;

            const deltaX = e.clientX - startX;
            const newWidth = startWidth + deltaX;
            
            // Limites: 200px mínimo, 600px máximo
            const minWidth = 200;
            const maxWidth = 600;
            
            if (newWidth >= minWidth && newWidth <= maxWidth) {
                sidebar.style.width = newWidth + 'px';
            }
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                resizer.classList.remove('resizing');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const resizer = document.getElementById('resizer');
        const floatingToggle = document.getElementById('floating-sidebar-toggle');
        const toggleBtn = document.getElementById('toggle-sidebar-btn');
        
        sidebar.classList.toggle('collapsed');
        
        if (sidebar.classList.contains('collapsed')) {
            resizer.classList.add('hidden');
            floatingToggle.classList.add('visible');
            toggleBtn.textContent = '▶';
        } else {
            resizer.classList.remove('hidden');
            floatingToggle.classList.remove('visible');
            toggleBtn.textContent = '◀';
        }
    }
}

// Initialize app
const app = new MxvizApp();
