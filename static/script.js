/**
 * AI命理教练网站交互脚本
 */

// 等待文档加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 获取表单和相关元素
    const birthdayForm = document.getElementById('birthdayForm');
    const generateBtn = document.getElementById('generateBtn');
    const loadingSection = document.getElementById('loadingSection');
    const reportSection = document.getElementById('reportSection');
    const reportContent = document.getElementById('reportContent');
    const baziInfoEl = document.getElementById('baziInfo');
    
    // 报告内容区域元素
    const overviewReport = document.getElementById('overviewReport');
    const tenGodsReport = document.getElementById('tenGodsReport');
    const actionGuideReport = document.getElementById('actionGuideReport');
    
    // 复制报告按钮
    const copyReportBtn = document.getElementById('copyReportBtn');
    
    // 保存图片按钮
    const saveImageBtn = document.getElementById('saveImageBtn');
    
    // 表单验证和提交处理
    birthdayForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 表单验证
        if (!birthdayForm.checkValidity()) {
            e.stopPropagation();
            birthdayForm.classList.add('was-validated');
            return;
        }
        
        // 获取表单数据
        const year = document.getElementById('year').value;
        const month = document.getElementById('month').value;
        const day = document.getElementById('day').value;
        const shichen = document.getElementById('shichen').value;
        
        // 显示加载动画，隐藏其他区域
        loadingSection.classList.remove('d-none');
        reportSection.classList.add('d-none');
        generateBtn.disabled = true;
        
        // 调用API生成报告
        generateReport(year, month, day, shichen);
    });
    
    /**
     * 调用后端API生成报告
     * @param {string} year - 年份
     * @param {string} month - 月份
     * @param {string} day - 日期
     * @param {string} shichen - 时辰
     */
    function generateReport(year, month, day, shichen) {
        // 准备请求数据
        const requestData = {
            year: year,
            month: month,
            day: day,
            shichen: shichen
        };
        
        // 发送API请求
        fetch('/generate_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络错误：' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            // 处理成功响应
            displayReport(data);
        })
        .catch(error => {
            // 处理错误
            console.error('生成报告出错:', error);
            alert('生成报告时出现错误：' + error.message);
        })
        .finally(() => {
            // 无论成功或失败，都重新启用按钮
            generateBtn.disabled = false;
            loadingSection.classList.add('d-none');
        });
    }
    
    /**
     * 显示生成的报告
     * @param {Object} data - API返回的数据
     */
    function displayReport(data) {
        // 确保有数据返回
        if (!data || !data.bazi_info || !data.reports) {
            alert('未能获取完整的报告数据');
            return;
        }
        
        // 显示报告部分
        reportSection.classList.remove('d-none');
        
        // 显示八字信息
        const baziInfo = data.bazi_info;
        baziInfoEl.textContent = `阳历：${baziInfo.solar_date} | 阴历：${baziInfo.lunar_date} | 八字：${baziInfo.bazi}`;
        
        // 填充八字信息可视化表格
        fillBaziChart(baziInfo);
        
        // 填充报告内容
        overviewReport.innerHTML = formatReportContent(data.reports.overview);
        tenGodsReport.innerHTML = formatReportContent(data.reports.ten_gods);
        actionGuideReport.innerHTML = formatReportContent(data.reports.action_guide);
        
        // 滚动到报告部分
        reportSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * 填充八字信息可视化表格
     * @param {Object} baziInfo - 八字信息数据
     */
    function fillBaziChart(baziInfo) {
        // 公历信息
        const solarParts = baziInfo.solar_date.split('年');
        document.getElementById('solar-year').textContent = solarParts[0];
        
        const monthDayParts = solarParts[1].split('月');
        document.getElementById('solar-month').textContent = monthDayParts[0];
        
        const dayTimeParts = monthDayParts[1].split('日');
        document.getElementById('solar-day').textContent = dayTimeParts[0];
        
        document.getElementById('solar-time').textContent = dayTimeParts[1].trim().replace('时', '');
        
        // 农历信息
        document.getElementById('lunar-year').textContent = baziInfo.lunar_year;
        document.getElementById('lunar-month').textContent = baziInfo.lunar_month;
        document.getElementById('lunar-day').textContent = baziInfo.lunar_day;
        document.getElementById('lunar-time').textContent = baziInfo.time_zhi;
        
        // 天干地支信息
        const ganElements = [
            {id: 'year-gan', value: baziInfo.year_gan},
            {id: 'month-gan', value: baziInfo.month_gan},
            {id: 'day-gan', value: baziInfo.day_gan},
            {id: 'time-gan', value: baziInfo.time_gan}
        ];
        
        const zhiElements = [
            {id: 'year-zhi', value: baziInfo.year_zhi},
            {id: 'month-zhi', value: baziInfo.month_zhi},
            {id: 'day-zhi', value: baziInfo.day_zhi},
            {id: 'time-zhi', value: baziInfo.time_zhi}
        ];
        
        // 注意：我们已经移除了十神信息行，所以不需要设置这些元素的文本内容
        
        // 设置天干颜色和文字
        ganElements.forEach(element => {
            const el = document.getElementById(element.id);
            el.textContent = element.value;
            el.className = 'gan-circle ' + getWuxingClass(element.value);
        });
        
        // 设置地支颜色和文字
        zhiElements.forEach(element => {
            const el = document.getElementById(element.id);
            el.textContent = element.value;
            el.className = 'zhi-circle ' + getWuxingClass(element.value);
        });
    }
    
    /**
     * 根据天干地支获取对应的五行类名
     * @param {string} char - 天干或地支字符
     * @return {string} 对应的CSS类名
     */
    function getWuxingClass(char) {
        // 天干五行对应
        const ganWuxing = {
            '甲': 'wuxing-mu', '乙': 'wuxing-mu',  // 甲乙属木
            '丙': 'wuxing-huo', '丁': 'wuxing-huo', // 丙丁属火
            '戊': 'wuxing-tu', '己': 'wuxing-tu',  // 戊己属土
            '庚': 'wuxing-jin', '辛': 'wuxing-jin', // 庚辛属金
            '壬': 'wuxing-shui', '癸': 'wuxing-shui' // 壬癸属水
        };
        
        // 地支五行对应
        const zhiWuxing = {
            '子': 'wuxing-shui', '亥': 'wuxing-shui', // 子亥属水
            '寅': 'wuxing-mu', '卯': 'wuxing-mu',   // 寅卯属木
            '午': 'wuxing-huo', '巳': 'wuxing-huo', // 午巳属火
            '申': 'wuxing-jin', '酉': 'wuxing-jin', // 申酉属金
            '辰': 'wuxing-tu', '戌': 'wuxing-tu',   // 辰戌属土
            '丑': 'wuxing-tu', '未': 'wuxing-tu'    // 丑未属土
        };
        
        return ganWuxing[char] || zhiWuxing[char] || '';
    }
    
    /**
     * 格式化报告内容，将Markdown和特殊格式转换为HTML
     * @param {string} content - 原始报告文本
     * @return {string} 格式化后的HTML内容
     */
    function formatReportContent(content) {
        if (!content) return '<p>无法生成内容，请稍后再试。</p>';
        
        // 处理代码块和特殊格式
        let processedContent = content
            // 处理代码块
            .replace(/```((?:\n|.)*?)```/g, function(match, codeContent) {
                return '<div class="code-block">' + codeContent.trim() + '</div>';
            })
            // 处理单行代码
            .replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // 首先将内容按行切分，以便我们可以逐行处理
        const lines = processedContent.split('\n');
        const processedLines = [];
        let inList = false;
        let listType = null; // 'ul' 或 'ol'
        let listIndentLevel = 0;
        
        // 逐行处理
        for (let i = 0; i < lines.length; i++) {
            let line = lines[i];
            
            // 处理标题
            if (line.match(/^#{1,6}\s/)) {
                const level = line.match(/^(#{1,6})\s/)[1].length;
                const title = line.replace(/^#{1,6}\s/, '');
                processedLines.push(`<h${level+1}>${title}</h${level+1}>`);
                continue;
            }
            
            // 处理水平线
            if (line.match(/^---+$/) || line.match(/^\*\*\*+$/)) {
                processedLines.push('<hr>');
                continue;
            }
            
            // 处理无序列表
            const ulMatch = line.match(/^(\s*)[\*\-]\s(.+)$/);
            if (ulMatch) {
                const indent = ulMatch[1].length;
                const content = ulMatch[2];
                
                if (!inList || listType !== 'ul') {
                    // 开始新的无序列表
                    if (inList) processedLines.push(listType === 'ol' ? '</ol>' : '</ul>');
                    processedLines.push('<ul>');
                    inList = true;
                    listType = 'ul';
                    listIndentLevel = indent;
                } else if (indent > listIndentLevel) {
                    // 嵌套列表
                    processedLines.push('<ul>');
                    listIndentLevel = indent;
                } else if (indent < listIndentLevel && indent === 0) {
                    // 结束嵌套列表
                    processedLines.push('</ul>');
                    listIndentLevel = indent;
                }
                
                processedLines.push(`<li>${formatInlineMarkdown(content)}</li>`);
                continue;
            }
            
            // 处理有序列表
            const olMatch = line.match(/^(\s*)\d+\.\s(.+)$/);
            if (olMatch) {
                const indent = olMatch[1].length;
                const content = olMatch[2];
                
                if (!inList || listType !== 'ol') {
                    // 开始新的有序列表
                    if (inList) processedLines.push(listType === 'ul' ? '</ul>' : '</ol>');
                    processedLines.push('<ol>');
                    inList = true;
                    listType = 'ol';
                    listIndentLevel = indent;
                } else if (indent > listIndentLevel) {
                    // 嵌套列表
                    processedLines.push('<ol>');
                    listIndentLevel = indent;
                } else if (indent < listIndentLevel && indent === 0) {
                    // 结束嵌套列表
                    processedLines.push('</ol>');
                    listIndentLevel = indent;
                }
                
                processedLines.push(`<li>${formatInlineMarkdown(content)}</li>`);
                continue;
            }
            
            // 如果当前行不是列表，但我们之前在列表中，则结束列表
            if (inList && !ulMatch && !olMatch && line.trim() !== '') {
                processedLines.push(listType === 'ul' ? '</ul>' : '</ol>');
                inList = false;
                listType = null;
            }
            
            // 空行处理
            if (line.trim() === '') {
                if (!inList) processedLines.push('<br>');
                continue;
            }
            
            // 其他普通文本行
            if (!inList) {
                processedLines.push(`<p>${formatInlineMarkdown(line)}</p>`);
            }
        }
        
        // 如果列表没有结束，确保结束它
        if (inList) {
            processedLines.push(listType === 'ul' ? '</ul>' : '</ol>');
        }
        
        return processedLines.join('');
    }
    
    /**
     * 格式化行内Markdown语法
     * @param {string} text - 要格式化的文本
     * @return {string} 格式化后的HTML
     */
    function formatInlineMarkdown(text) {
        return text
            // 保留特殊符号（如黑点、箭头等）
            .replace(/&#10004;/g, '✔') // 勾选标记
            .replace(/&#9642;/g, '▪') // 小黑方块
            .replace(/&#9679;/g, '●') // 黑点
            .replace(/&#8594;/g, '→') // 右箭头
            // 加粗
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // 斜体
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // 下划线
            .replace(/__(.*?)__/g, '<u>$1</u>')
            // 删除线
            .replace(/~~(.*?)~~/g, '<del>$1</del>')
            // 链接
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
    }
    
    // 复制报告功能
    copyReportBtn.addEventListener('click', function() {
        // 创建一个临时文本区域
        const textArea = document.createElement('textarea');
        
        // 收集所有报告文本
        const reportText = [
            '【八字命盘概览】',
            overviewReport.textContent.trim(),
            '\n\n【十神深度探索】',
            tenGodsReport.textContent.trim(),
            '\n\n【赋能行动手册】',
            actionGuideReport.textContent.trim(),
            '\n\n生成时间：' + new Date().toLocaleString('zh-CN')
        ].join('\n');
        
        // 设置文本区域内容并添加到文档
        textArea.value = reportText;
        document.body.appendChild(textArea);
        
        // 选择并复制内容
        textArea.select();
        document.execCommand('copy');
        
        // 移除临时文本区域
        document.body.removeChild(textArea);
        
        // 显示复制成功提示
        alert('报告已复制到剪贴板！');
    });
    
    // 保存为图片功能
    saveImageBtn.addEventListener('click', function() {
        html2canvas(reportContent, {
            scale: 2, // 提高图片质量
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#f5f5f5',
            logging: false
        }).then(canvas => {
            // 创建图片链接
            const link = document.createElement('a');
            link.download = '命理报告_' + new Date().toISOString().slice(0, 10) + '.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
        }).catch(err => {
            console.error('保存图片时出错:', err);
            alert('保存图片时出现错误，请稍后再试');
        });
    });
    
    // 动态更新日期选择器中的天数
    function updateDays() {
        const yearSelect = document.getElementById('year');
        const monthSelect = document.getElementById('month');
        const daySelect = document.getElementById('day');
        
        // 如果年份和月份都已选择
        if (yearSelect.value && monthSelect.value) {
            const year = parseInt(yearSelect.value);
            const month = parseInt(monthSelect.value);
            
            // 获取当月天数
            const daysInMonth = new Date(year, month, 0).getDate();
            
            // 保存当前选择的日期
            const currentDay = daySelect.value;
            
            // 清空日期选择器
            daySelect.innerHTML = '';
            
            // 添加"选择日期"选项
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.disabled = true;
            defaultOption.selected = !currentDay;
            defaultOption.textContent = '选择日期';
            daySelect.appendChild(defaultOption);
            
            // 添加天数选项
            for (let i = 1; i <= daysInMonth; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = i + '日';
                option.selected = (currentDay && parseInt(currentDay) === i);
                daySelect.appendChild(option);
            }
        }
    }
    
    // 当年份或月份变化时更新日期
    document.getElementById('year').addEventListener('change', updateDays);
    document.getElementById('month').addEventListener('change', updateDays);
    
    // 初始更新一次日期（如果有预设值）
    updateDays();
});
