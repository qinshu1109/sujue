#!/usr/bin/env node

/**
 * i18n覆盖率检查脚本
 * 女娲造物：精工细作，一字不差
 */

const fs = require('fs');
const path = require('path');

// 配置
const CONFIG = {
  srcDir: path.join(__dirname, '../src'),
  excludePatterns: [
    'locales',     // 排除语言包文件
    'i18n',        // 排除i18n配置
    'mockApi.js',  // 排除Mock文件
    'node_modules',
    'build',
    'dist'
  ],
  fileExtensions: ['jsx', 'js', 'ts', 'tsx'],
  chinesePattern: /[\u4e00-\u9fa5]+/g,
  excludeConsoleLog: true,
  excludeComments: true
};

class I18nLinter {
  constructor() {
    this.results = {
      totalFiles: 0,
      checkedFiles: 0,
      hardcodedStrings: [],
      missingKeys: [],
      coverage: 0,
      recommendations: []
    };
  }

  // 递归扫描文件
  scanFiles() {
    const files = this.getAllFiles(CONFIG.srcDir);
    
    this.results.totalFiles = files.length;
    
    files.forEach(file => {
      this.checkFile(file);
    });
    
    this.calculateCoverage();
    this.generateRecommendations();
  }

  // 递归获取所有文件
  getAllFiles(dir) {
    let results = [];
    
    try {
      const list = fs.readdirSync(dir);
      
      list.forEach(file => {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        
        if (stat && stat.isDirectory()) {
          // 检查是否为排除目录
          const shouldExclude = CONFIG.excludePatterns.some(pattern => 
            file.includes(pattern) || fullPath.includes(pattern)
          );
          
          if (!shouldExclude) {
            // 递归子目录
            results = results.concat(this.getAllFiles(fullPath));
          }
        } else {
          // 检查是否为排除文件
          const shouldExclude = CONFIG.excludePatterns.some(pattern => 
            file.includes(pattern) || fullPath.includes(pattern)
          );
          
          if (!shouldExclude) {
            // 检查文件扩展名
            const ext = path.extname(file).slice(1);
            if (CONFIG.fileExtensions.includes(ext)) {
              results.push(fullPath);
            }
          }
        }
      });
    } catch (error) {
      console.error(`Error reading directory ${dir}:`, error.message);
    }
    
    return results;
  }

  // 检查单个文件
  checkFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const relativePath = path.relative(CONFIG.srcDir, filePath);
      
      this.results.checkedFiles++;
      
      // 查找硬编码中文
      const lines = content.split('\n');
      
      lines.forEach((line, lineNum) => {
        // 跳过注释行
        if (CONFIG.excludeComments && (line.trim().startsWith('//') || line.trim().startsWith('*'))) {
          return;
        }
        
        // 跳过console.log
        if (CONFIG.excludeConsoleLog && line.includes('console.')) {
          return;
        }
        
        const chineseMatches = line.match(CONFIG.chinesePattern);
        if (chineseMatches) {
          chineseMatches.forEach(match => {
            this.results.hardcodedStrings.push({
              file: relativePath,
              line: lineNum + 1,
              text: match,
              context: line.trim()
            });
          });
        }
      });
      
      // 检查是否使用了useTranslation
      const usesTranslation = content.includes('useTranslation') || content.includes('t(');
      
      if (chineseMatches && chineseMatches.length > 0 && !usesTranslation) {
        this.results.missingKeys.push({
          file: relativePath,
          issue: 'Contains Chinese text but missing useTranslation'
        });
      }
      
    } catch (error) {
      console.error(`Error reading file ${filePath}:`, error.message);
    }
  }

  // 计算覆盖率
  calculateCoverage() {
    const totalIssues = this.results.hardcodedStrings.length + this.results.missingKeys.length;
    const maxPossibleIssues = this.results.checkedFiles * 2; // 假设每个文件最多2个问题
    
    this.results.coverage = Math.max(0, 100 - (totalIssues / maxPossibleIssues * 100));
    
    // 如果没有硬编码问题，直接给高分
    if (totalIssues === 0) {
      this.results.coverage = 95; // 给95分，预留5分给完善空间
    }
  }

  // 生成建议
  generateRecommendations() {
    if (this.results.hardcodedStrings.length > 0) {
      this.results.recommendations.push(
        `发现 ${this.results.hardcodedStrings.length} 个硬编码中文字符串，建议迁移到 locales/ 文件`
      );
    }
    
    if (this.results.missingKeys.length > 0) {
      this.results.recommendations.push(
        `${this.results.missingKeys.length} 个文件缺少 useTranslation hook`
      );
    }
    
    if (this.results.coverage >= 90) {
      this.results.recommendations.push('✅ 国际化覆盖率优秀！建议继续保持');
    } else if (this.results.coverage >= 60) {
      this.results.recommendations.push('⚠️ 国际化覆盖率良好，还需改进部分文案');
    } else {
      this.results.recommendations.push('❌ 国际化覆盖率不足，需要大量改进');
    }
  }

  // 生成报告
  generateReport() {
    const report = {
      summary: {
        检查文件数: this.results.checkedFiles,
        覆盖率: `${this.results.coverage.toFixed(1)}%`,
        硬编码问题: this.results.hardcodedStrings.length,
        缺失Hook: this.results.missingKeys.length
      },
      details: {
        hardcodedStrings: this.results.hardcodedStrings,
        missingKeys: this.results.missingKeys
      },
      recommendations: this.results.recommendations,
      generatedAt: new Date().toISOString(),
      passThreshold: this.results.coverage >= 60 ? '✅ PASS' : '❌ FAIL'
    };
    
    return report;
  }

  // 输出到控制台
  printReport() {
    const report = this.generateReport();
    
    console.log('\n🔍 i18n 国际化覆盖率报告');
    console.log('='.repeat(50));
    
    Object.entries(report.summary).forEach(([key, value]) => {
      console.log(`${key}: ${value}`);
    });
    
    console.log('\n📋 详细问题:');
    if (report.details.hardcodedStrings.length > 0) {
      console.log('\n硬编码中文字符串:');
      report.details.hardcodedStrings.forEach((item, index) => {
        console.log(`  ${index + 1}. ${item.file}:${item.line} - "${item.text}"`);
      });
    }
    
    if (report.details.missingKeys.length > 0) {
      console.log('\n缺失 useTranslation:');
      report.details.missingKeys.forEach((item, index) => {
        console.log(`  ${index + 1}. ${item.file} - ${item.issue}`);
      });
    }
    
    console.log('\n💡 建议:');
    report.recommendations.forEach((rec, index) => {
      console.log(`  ${index + 1}. ${rec}`);
    });
    
    console.log(`\n${report.passThreshold}`);
    console.log('='.repeat(50));
    
    return report.passThreshold.includes('✅');
  }

  // 保存报告到文件
  saveReport(outputPath) {
    const report = this.generateReport();
    const reportPath = outputPath || path.join(__dirname, '../i18n-coverage-report.json');
    
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`\n📄 报告已保存到: ${reportPath}`);
  }
}

// 主执行函数
function main() {
  const linter = new I18nLinter();
  
  console.log('🚀 开始 i18n 覆盖率检查...');
  linter.scanFiles();
  
  const passed = linter.printReport();
  
  // 保存报告
  linter.saveReport();
  
  // 根据结果设置退出码
  process.exit(passed ? 0 : 1);
}

// 如果直接运行此脚本
if (require.main === module) {
  main();
}

module.exports = I18nLinter;