# pygame_dialog

Provides classes for making user interface dialogs with pygame, including
GridLayout, HorizontalLayout, VerticalLayout, Label, Button, Textbox, Radio,
and Dialog.

As of this initial commmit, this code can only produce standalone dialogs. It
would be nice to be able to create a dialog which can "dock" to part of the
pygame display. (For future development!)

You can generate a dialog by passing the definition to the Dialog constructor:

	dialog = Dialog(
		Textbox("Some text goes here.", align=ALIGN_LEFT, width=360),
		Button("Bottom Button", padding=22, click_handler=do_something),
		status_label
	)

Alternately, you can subclass Dialog, and define the layout in the constructor:

	class MyDialog(Dialog):

		def __init__(self):
			Dialog.__init__(self)
			for idx in range(4):
				self.append(Button(
					"",
					font_size = 20,
					padding = 12,
					margin = (2,10),
					click_handler = self._button_click,
					disabled = True,
				))

## Layouts

The layout of a dialog is defined by the GridLayout, HorizontalLayout, and
VerticalLayout classes. Each of these can contain another "widgets" or other
layouts. (If you've done any PyQt programming this should sound familiar). Each
of these elements can have their own margin, padding, foreground and background
colors.

The layouts calculate the size necessary to render the widgets/layouts
contained within. Once the area is defined, the contained widgets/layouts are
expanded too fill the aread available to them. The result is usually pretty
aesthetic.

When creating a Dialog, you can define Layouts which contain Layouts, like so:

	dialog = Dialog(
		HorizontalLayout(
			VerticalLayout(
				Button("Button One", click_handler=some_function),
				Button("Button Two", click_handler=some_function),
				Button("Button Three", click_handler=some_function)
			),
			VerticalLayout(
				Button("Button Four", click_handler=some_function),
				Button("Button Five", click_handler=some_function),
				Button("Button Six", click_handler=some_function)
			)
		),
		Button("Bottom button", click_handler=some_function),
	)


## Widgets

The available widgets include Label, Button, Textbox, and Radio. That's kinda
minimal, but expanding it is pretty easy. Anyone care to give it a shot, go for
it.

All the widgets have a default visual appearance, which is an inset "bevel"
effect for a Textbox, and an outset bevel effect with a wider margin for a
Button. It's possible to override the bevel effect with a different effect,
such as rounded corners. That effect is built-in, and you can see examples of
it by running the module at the command line with the appropriate options.

Navigation between widgets using TAB and SHIFT-TAB is available as well, the
tab order being determined by the order in which Widgets appear in their
container layouts, and the order in which contained layouts appear in their
containing layout. Visual feedback is provided by changing the foreground and
background color of the "focused" Widget.

### Textbox

Allows user input by handling keyboard events. Allows for CTRL-right and
CTRL-left navigation by word, as well as SHIFT-CTRL-left and SHIFT-CTRL-right
selection of text, CTRL-a "select all", DELETE and BACKSPACE. A "text entry
cursor" effect is accomplished by using a custom pygame cursor. The "text"
attribute is made available to utilize what the user has typed in your game.

### Button

The Dialog class determine where the mouse is with respect to all of the
contained elements, and detect when the mouse goes down and back up over the
Button element, triggering the callback function provided to the Button
constructor.

### Radio

Typical Radio button class. You pass a "group" id to the constructor, and the
"selected" attribute of all the Radio instances with that same group are
mutually exclusive. Generates "click events" just like a button, so you can
modify other parts of the dialog when selection changes.

You can query which Radio in a group is selected using the
Radio.selected_element(<group>) class method. Get the value of the selected
Radio in a group using the Radio.selected_value(<group>) class method.

The "value" attribute of a Radio is optional; if no "value" is set, "value"
returns the text of the Radio's label.


### Widget attributes:

All classes which subclass "Widget" utilize the following attributes:

| attribute						| Description 	|
|-------------------------------|---------------|
|	margin						| Minimum distance between this Widget and it neighbors/dialog border |
|	padding						| Space inside this Widget's painted area |
|	foreground_color			| The normal foreground text color when not hovered or "disabled" |
|	foreground_color_hover		| The foreground text color when the mouse hovers over |
|	foreground_color_focus		| The foreground text color when the Widget is focused using the TAB key |
|	foreground_color_disabled	| The foreground text color when the Widget is "disabled" under programmatic control |
|	background_color			| The normal background text color when not hovered or "disabled" |
|	background_color_hover		| The background text color when the mouse hovers over |
|	background_color_focus		| The background text color when the Widget is focused using the TAB key |
|	background_color_disabled	| The background text color when the Widget is "disabled" under programmatic control |
|	disabled					| State flag which identifies the Widget as being "disabled" - you set this. |
|	hovering					| State flag which identifies the Widget as being "disabled" - the Dialog class sets this. ||
|	focused						| State flag which identifies the Widget as being "focused" - the Dialog class sets this. ||

### Commmon Widget events

All the widgets provide the following functions, which are called from the Dialog main loop. That's where you'll be putting your custom code:

| function			| Description 	|
|-------------------|---------------|
|	mouse_in		| Called when the mouse enters the area of the Widget, (not including its margin) |
|	mouse_out		| Called when the mouse leaves the area of the Widget, (not including its margin) |
|	click			| Called when the mouse button went down, and then up, within the area of the Widget, (not including its margin) |

# Screenshots:

Here's some screenshots, and the commands used to create them:

	$ python3 pygame_dialog.py

![basic dialog](https://github.com/Zen-Master-SoSo/pygame_dialog/blob/main/screenshots/dialog.png?raw=true)

	$ python3 pygame_dialog.py -r

![basic dialog with rounded Widgets](https://github.com/Zen-Master-SoSo/pygame_dialog/blob/main/screenshots/roundies.png?raw=true)

	$ python3 pygame_dialog.py -g

![grid dialog](https://github.com/Zen-Master-SoSo/pygame_dialog/blob/main/screenshots/grid.png?raw=true)

	$ python3 pygame_dialog.py -gr

![grid dialog with rounded Widgets](https://github.com/Zen-Master-SoSo/pygame_dialog/blob/main/screenshots/grid-roundies.png?raw=true)


