import importlib
import importlib.util
import re
from pathlib import Path

import streamlit as st

# Runner page: sidebar navigation that loads page modules dynamically.
st.set_page_config(page_title="IND320 App", layout="wide")

st.title("IND320 Streamlit App")
st.write("Use the sidebar to navigate between pages.")


# Helper: discover page modules under two possible folders
def discover_pages():
	"""Return a list of (module_name, display_name, path) for pages found."""
	candidates = []
	roots = [Path(__file__).parent / "Pages", Path(__file__).parent / "DataApp" / "Pages"]
	for root in roots:
		if not root.exists():
			continue
		for py in sorted(root.glob("*.py")):
			name = py.stem
			# create a display name: remove leading digits/underscores/hyphens then prettify
			display_raw = re.sub(r'^[\d_\-\s]+', '', name)
			display = display_raw.replace("_", " ").title()
			# module path for importlib (use a dynamic spec)
			module_name = f"{py.parent.name}.{name}"
			candidates.append((module_name, display, str(py)))
	return candidates


# Discover pages
pages = discover_pages()

# Sidebar navigation
st.sidebar.title("Navigation")

# Initialize session state for current page
if 'page' not in st.session_state:
	st.session_state['page'] = 'Home'

# Home button
if st.sidebar.button("Home", key="nav_home"):
	st.session_state['page'] = 'Home'

# One button per discovered page (no numbers in the display names)
for i, (_mod, display, path) in enumerate(pages):
	if st.sidebar.button(display, key=f"nav_{i}"):
		st.session_state['page'] = path


def load_module_from_path(path_str: str, module_alias: str):
	"""Import a module given a file path using importlib and return the module."""
	spec = importlib.util.spec_from_file_location(module_alias, path_str)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


current = st.session_state.get('page', 'Home')

if current == "Home":
	# Show a simple home page with a preview (load Data_loader if available)
	st.header("Home")
	try:
		from Data_loader import load_data

		df = load_data()
		st.subheader("Preview (first 10 rows)")
		st.dataframe(df.head(10), use_container_width=True)
		st.write(f"Data has {len(df)} rows and {len(df.columns)} columns.")
	except Exception as e:
		st.warning("Could not load data preview: " + str(e))

else:
	# Find the page by file path stored in session state
	match = None
	for mod_name, display, path in pages:
		if path == current:
			match = (mod_name, display, path)
			break
	if match is None:
		st.error("Page not found or not discovered")
	else:
		mod_name, display, path = match
		st.header(display)
		try:
			module = load_module_from_path(path, mod_name)
			# Call main() if present, otherwise importing executed the page already
			if hasattr(module, "main") and callable(module.main):
				module.main()
		except Exception as e:
			st.error(f"Error loading page {display}: {e}")