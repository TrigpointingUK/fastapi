export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-800 text-gray-300 sticky bottom-0 z-40 border-t border-gray-700">
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* About Section */}
          <div>
            <h3 className="text-white font-bold text-base mb-2">Trigpointing UK</h3>
            <p className="text-xs">
              The UK's premier resource for triangulation pillars and survey markers.
              Join thousands of enthusiasts exploring Britain's geodetic heritage.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-bold text-base mb-2">Quick Links</h3>
            <nav className="space-y-1 text-xs">
              <a
                href="https://wiki.trigpointing.uk/"
                target="_blank"
                rel="noopener noreferrer"
                className="block hover:text-white"
              >
                Wiki
              </a>
              <a
                href="https://forum.trigpointing.uk/"
                target="_blank"
                rel="noopener noreferrer"
                className="block hover:text-white"
              >
                Forum
              </a>
              <a
                href="https://trigpointing.uk/trigtools"
                target="_blank"
                rel="noopener noreferrer"
                className="block hover:text-white"
              >
                TrigTools
              </a>
            </nav>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-white font-bold text-base mb-2">Legal</h3>
            <nav className="space-y-1 text-xs">
              <a href="/about" className="block hover:text-white">
                About
              </a>
              <a href="/privacy" className="block hover:text-white">
                Privacy Policy
              </a>
              <a href="/terms" className="block hover:text-white">
                Terms of Service
              </a>
              <a href="/contact" className="block hover:text-white">
                Contact Us
              </a>
            </nav>
          </div>
        </div>

        <div className="border-t border-gray-700 mt-4 pt-3 text-center text-xs">
          <p>&copy; {currentYear} Trigpointing UK. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

