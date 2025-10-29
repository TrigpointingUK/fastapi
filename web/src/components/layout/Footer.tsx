export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-800 text-gray-300 mt-12">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About Section */}
          <div>
            <h3 className="text-white font-bold text-lg mb-3">Trigpointing UK</h3>
            <p className="text-sm">
              The UK's premier resource for triangulation pillars and survey markers.
              Join thousands of enthusiasts exploring Britain's geodetic heritage.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-bold text-lg mb-3">Quick Links</h3>
            <nav className="space-y-2 text-sm">
              <a
                href="https://trigpointing.uk/wiki"
                target="_blank"
                rel="noopener noreferrer"
                className="block hover:text-white"
              >
                Wiki
              </a>
              <a
                href="https://trigpointing.uk/forum"
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
            <h3 className="text-white font-bold text-lg mb-3">Legal</h3>
            <nav className="space-y-2 text-sm">
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

        <div className="border-t border-gray-700 mt-8 pt-6 text-center text-sm">
          <p>&copy; {currentYear} Trigpointing UK. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

