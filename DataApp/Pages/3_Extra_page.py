import streamlit as st

st.title("Extra Page")

if 'show_video' not in st.session_state:
    st.session_state['show_video'] = False

def show_video():
    st.session_state['show_video'] = True

st.button("Do Not Press", on_click=show_video)

if st.session_state['show_video']:
    # Embed YouTube with autoplay=1 and mute=1 for best compatibility
    st.components.v1.iframe(
        "https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1&mute=1",
        height=315,
        width=560
    )

#when video done playing, remove button 
    st.button("Reset", on_click=lambda: st.session_state.update({'show_video': False}))
    st.write("Video finished playing. You can reset the button.")
else:
    st.write("Press it at your own risk.")
#when video done playing, add a new button to maria carey video
    if st.button("DO NOT PRESS! IT IS TO EARLY!"):
        st.components.v1.iframe(
            "https://www.youtube.com/embed/aAkMkVFwAoo?autoplay=1&mute=1",
            height=315,
            width=560
        )
        st.button("Reset", on_click=lambda: st.session_state.update({'show_video': False}))
        st.write("You pressed it, you monster!")