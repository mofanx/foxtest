const { mergeCoverageReports } = require('monocart-coverage-reports');
const fs = require('fs');
const path = require('path');

const coverageDir = path.join(__dirname, 'coverage');
const coverageFile = path.join(coverageDir, 'coverage.json');
const outputFile = path.join(coverageDir, 'lcov.info');

if (!fs.existsSync(coverageFile)) {
  console.log('覆盖数据文件不存在:', coverageFile);
  process.exit(1);
}

// 读取 V8 覆盖数据
const coverage = JSON.parse(fs.readFileSync(coverageFile, 'utf-8'));

// 使用 monocart 转换
mergeCoverageReports([
  {
    name: 'Demo Site Coverage',
    code: JSON.stringify(coverage),
    source: {
      // 指向 demo-site 目录作为源代码根目录
      path: path.join(__dirname, '../demo-site')
    }
  }
], {
  outputDir: coverageDir,
  reports: [['lcov'], ['html']]
}).then(() => {
  console.log('覆盖报告已生成到:', coverageDir);
}).catch(err => {
  console.error('生成覆盖报告失败:', err);
  process.exit(1);
});