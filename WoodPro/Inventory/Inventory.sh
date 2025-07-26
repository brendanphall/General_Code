#!/bin/bash

# Technology Stack Inventory Script for WoodPro Application
# This script analyzes file types, dependencies, and identifies outdated components

echo "=== WOODPRO TECHNOLOGY INVENTORY ==="
echo "Generated on: $(date)"
echo "Repository: $(basename $(pwd))"
echo ""

# 1. File Type Analysis
echo "1. FILE TYPE BREAKDOWN:"
echo "========================="
find . -type f -name ".*" -prune -o -type f -print | grep -E '\.[a-zA-Z0-9]+$' | sed 's/.*\.//' | sort | uniq -c | sort -nr
echo ""

# 2. JavaScript Analysis
echo "2. JAVASCRIPT ANALYSIS:"
echo "========================"
echo "Total JS files: $(find . -name "*.js" -type f | wc -l)"
echo "JavaScript file sizes:"
find . -name "*.js" -type f -exec du -h {} + | sort -hr | head -20
echo ""

# 3. Check for specific outdated patterns
echo "3. OUTDATED TECHNOLOGY DETECTION:"
echo "=================================="

# Dojo Toolkit detection
echo "Dojo Toolkit usage:"
grep -r "dojo\." --include="*.js" --include="*.html" . | wc -l
echo "  - References found: $(grep -r "dojo\." --include="*.js" --include="*.html" . | wc -l)"

# AMD module detection
echo "AMD module patterns:"
echo "  - define() calls: $(grep -r "define(" --include="*.js" . | wc -l)"
echo "  - require() calls: $(grep -r "require(" --include="*.js" . | wc -l)"

# ASP.NET Web Forms detection
echo "ASP.NET Web Forms:"
echo "  - .aspx files: $(find . -name "*.aspx" | wc -l)"
echo "  - .ascx files: $(find . -name "*.ascx" | wc -l)"
echo "  - .master files: $(find . -name "*.master" | wc -l)"

# .NET Framework version detection
echo ".NET Framework versions:"
grep -r "targetFramework" --include="*.config" --include="*.csproj" . | head -10

# ArcGIS SDK detection
echo "ArcGIS SDK references:"
grep -r "arcgis" --include="*.js" --include="*.html" --include="*.config" . | head -10
echo ""

# 4. Dependency Analysis
echo "4. DEPENDENCY FILES:"
echo "===================="
echo "Package.json files:"
find . -name "package.json" -exec echo "  {}" \; -exec head -20 {} \;
echo ""
echo "NuGet packages.config files:"
find . -name "packages.config" -exec echo "  {}" \; -exec cat {} \;
echo ""
echo "Project files (.csproj):"
find . -name "*.csproj" -exec echo "  {}" \; -exec head -30 {} \;
echo ""

# 5. Build System Analysis
echo "5. BUILD SYSTEM:"
echo "================"
echo "Build-related files found:"
find . -name "gulpfile.js" -o -name "webpack.config.js" -o -name "rollup.config.js" -o -name "Gruntfile.js" -o -name "*.build.js" -o -name "build.js" | head -10
echo ""

# 6. CSS/Styling Analysis
echo "6. STYLING ANALYSIS:"
echo "==================="
echo "CSS files: $(find . -name "*.css" | wc -l)"
echo "SCSS/SASS files: $(find . -name "*.scss" -o -name "*.sass" | wc -l)"
echo "LESS files: $(find . -name "*.less" | wc -l)"
echo ""

# 7. Database/Config Files
echo "7. CONFIGURATION FILES:"
echo "======================="
echo "Web.config files:"
find . -name "web.config" -exec echo "  {}" \; -exec grep -i "targetFramework\|compilation\|membership" {} \;
echo ""

# 8. Security-related files
echo "8. SECURITY ANALYSIS:"
echo "===================="
echo "Authentication/Authorization patterns:"
grep -r "AspNetSqlMembershipProvider\|membership\|authentication" --include="*.config" --include="*.cs" . | head -10
echo ""

# 9. Third-party libraries
echo "9. THIRD-PARTY LIBRARIES:"
echo "========================="
echo "Common library references:"
grep -r "jquery\|bootstrap\|angular\|react\|vue" --include="*.js" --include="*.html" . | head -10
echo ""

# 10. File structure overview
echo "10. DIRECTORY STRUCTURE:"
echo "========================"
tree -d -L 3 . 2>/dev/null || find . -type d -name ".*" -prune -o -type d -print | head -20
echo ""

echo "=== INVENTORY COMPLETE ==="
echo "For detailed analysis, examine the files mentioned above."
echo "Pay special attention to:"
echo "- Package.json for JavaScript dependencies"
echo "- Web.config for .NET Framework settings"
echo "- .csproj files for project configuration"
echo "- Large JavaScript files for legacy patterns"