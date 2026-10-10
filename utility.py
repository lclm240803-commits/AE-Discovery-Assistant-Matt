import hmac
import streamlit as st

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Do not store the plain password in session state
        else:
            st.session_state["password_correct"] = False

    # Return True if the password has already been verified
    if st.session_state.get("password_correct", False):
        return True

    # Show input prompt for password
    st.text_input(
        "Enter Password to access the AE Discovery Assistant:",
        type="password",
        on_change=password_entered,
        key="password",
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect. Please try again.")
    return False