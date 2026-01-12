import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl">📈</span>
              <span className="font-bold text-lg text-gray-900">Macro Skills</span>
            </div>
            <p className="mt-2 text-sm text-gray-600">
              專注於宏觀經濟分析的技能市集 (Claude Code)
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">連結</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/skills" className="text-sm text-gray-600 hover:text-gray-900">
                  瀏覽技能
                </Link>
              </li>
              <li>
                <Link to="/docs" className="text-sm text-gray-600 hover:text-gray-900">
                  文件說明
                </Link>
              </li>
              <li>
                <Link to="/submit" className="text-sm text-gray-600 hover:text-gray-900">
                  提交技能
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">資源</h3>
            <ul className="space-y-2">
              <li>
                <a
                  href="https://github.com/fatfingererr/macro-skills"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  GitHub
                </a>
              </li>
              <li>
                <a
                  href="https://claude.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  Claude
                </a>
              </li>
              <li>
                <a
                  href="https://discord.gg/zReHspPEzZ"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  Discord
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200">
          <p className="text-center text-sm text-gray-500">
            &copy; {new Date().getFullYear()} Macro Skills. MIT License.
          </p>
        </div>
      </div>
    </footer>
  );
}
