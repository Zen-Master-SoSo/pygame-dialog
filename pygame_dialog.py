"""
Provides classes for making user interface dialogs with pygame, including
GridLayout, LinearLayout, HorizontalLayout, VerticalLayout, TextWidget, Label,
Button, Textbox, and Dialog
"""

import pygame, os
from math import pi
from pygame import Rect, Color, Surface, display
from pygame.math import Vector2 as Vector
from pygame.draw import polygon, circle, line, arc
from pygame.locals import *


ALIGN_CENTER		= 0
ALIGN_LEFT			= 1
ALIGN_RIGHT			= 2

STATE_NORMAL		= 0
STATE_HOVER			= 1
STATE_FOCUS			= 2

NO_POSITION			= (-1, -1)

RADIANS_BOTTOM_LEFT	= pi * 0.25
RADIANS_TOPRIGHT	= pi * 1.25



class Layout:
	"""
	Base class of HorizontalLayout, VerticalLayout, and GridLayout.
	"""

	rect	= None


	def get_initial_rect(self):
		"""
		Determine the minimum space necessary for this element and its' contained elements.
		Returns Rect
		"""
		pass


	def justify_elements(self):
		"""
		Expand the area allowed to each element so that they fill available space.
		"""
		pass


	def position_rects(self):
		"""
		Set the final top, left position of contained elements.
		"""
		pass


	def widgets(self):
		"""
		A generator function which yields all the Widget instances contained in this Layout.
		"""
		pass


	def widget_at(self, pos):
		"""
		Returns the Widget at the given screen position (which is usually the mouse position).
		"""
		pass


	def focusable_widgets(self):
		"""
		Returns a list of widgets contained in this layout which may receieve the focus.
		"""
		return filter(lambda elem: not isinstance(elem, Label) and not elem.disabled, self.widgets())


	def focusable_widget_before(self, widget):
		"""
		Returns the Widget preceeding widget, irrespective of container.
		"""
		prev = None
		for e in self.focusable_widgets():
			if e is widget:
				return prev
			prev = e
		return None


	def focusable_widget_after(self, widget):
		"""
		Returns the Widget following widget, irrespective of container.
		"""
		elem_found = False
		for e in self.focusable_widgets():
			if elem_found:
				return e
			elif e is widget:
				elem_found = True
		return None


	def first_focusable_widget(self):
		"""
		Returns the first Widget, irrespective of container.
		"""
		for e in self.focusable_widgets(): return e


	def last_focusable_widget(self):
		"""
		Returns the last Widget, irrespective of container.
		"""
		for e in self.focusable_widgets(): pass
		return e


	def __str__(self):
		return "%s (%d x %d) @ (%d, %d)" % (
			self.__class__.__name__,
			self.rect.width, self.rect.height, self.rect.left, self.rect.top
		)



class GridLayout(Layout):
	"""
	A container for other elements, including layouts and widgets, which arranges them in a grid.
	"""


	def __init__(self, *args):
		self.rows = []
		for arg in args:
			self.append(arg)


	def append(self, arg):
		"""
		Add a row to this GridLayout.
		Accepts a list of elements (Widget or Layout). Returns this GridLayout.
		"""
		if type(arg) != list: raise Exception("GridLayout takes only lists as arguments")
		self.rows.append(arg)
		return self


	def __getattr__(self, varname):
		"""
		Retrieve margin values of this Layout from its contained elements.
		"""
		if varname == "margin_top":
			return self.row_margins[0]
		elif varname == "margin_right":
			return self.column_margins[-1]
		elif varname == "margin_bottom":
			return self.row_margins[-1]
		elif varname == "margin_left":
			return self.column_margins[0]


	def get_initial_rect(self):
		"""
		Determine the minimum space necessary for this element and its' contained elements.
		Returns Rect
		"""
		self.row_count = len(self.rows)
		self.column_count = 0
		for row in self.rows: self.column_count = max(self.column_count, len(row))
		self.rect = Rect((0, 0, 0, 0))
		self.column_widths = [0] * self.column_count
		self.row_heights = [0] * self.row_count
		self.column_margins = [0] * (self.column_count + 1)	# Include margin to the left of column 0, and to the right of last
		self.row_margins = [0] * (self.row_count + 1)	# Include margin above row 0, and below the last
		prev_row = None
		for r in range(self.row_count):
			row = self.rows[r]
			for c in range(self.column_count):
				if c == len(row): continue	# No cell at this column in this row
				rect = row[c].get_initial_rect()
				self.column_widths[c] = max(self.column_widths[c], rect.width)
				self.row_heights[r] = max(self.row_heights[r], rect.height)
				# Determine row margin:
				if r == 0:
					# self.row_margins[0] is the margin ABOVE the first row
					self.row_margins[0] = max(self.row_margins[0], row[c].margin_top)
				elif c < len(prev_row):	# Don't check a cell in the previous row which doesn't exist
					self.row_margins[r] = max(self.row_margins[r], prev_row[c].margin_bottom, row[c].margin_top)
				# Determine column margin:
				if c == 0:
					# self.column_margins[0] is the margin to the LEFT of the first column
					margin = row[c].margin_left
				else:
					margin = max(row[c - 1].margin_right, row[c].margin_left)
				self.column_margins[c] = max(self.column_margins[c], margin)
			# Finished looping through columns, now set the right-most margin:
			if len(row) == self.column_count:
				self.column_margins[self.column_count] = \
					max(self.column_margins[self.column_count], row[self.column_count - 1].margin_right)
			prev_row = row
		# Finished looping through rows, now set the bottom-most margin:
		self.row_margins[self.row_count] = max(cell.margin_bottom for cell in self.rows[self.row_count - 1])
		self.rect.width = sum(self.column_widths) + sum(self.column_margins[1:-1])
		self.rect.height = sum(self.row_heights) + sum(self.row_margins[1:-1])
		return self.rect


	def justify_elements(self):
		"""
		Expand the area allowed to each element so that they fill available space.
		"""
		for r in range(self.row_count):
			for c in range(self.column_count):
				if c == len(self.rows[r]): continue
				self.rows[r][c].rect.width = self.column_widths[c]
				self.rows[r][c].rect.height = self.row_heights[r]
				if isinstance(self.rows[r][c], Layout):
					self.rows[r][c].justify_elements()


	def position_rects(self):
		"""
		Set the final top, left position of contained elements.
		"""
		tops = [self.rect.top for i in range(self.row_count)]
		lefts = [self.rect.left for i in range(self.column_count)]
		for r in range(1, self.row_count):
			tops[r] = tops[r - 1] + self.row_heights[r - 1] + self.row_margins[r]
		for c in range(1, self.column_count):
			lefts[c] = lefts[c - 1] + self.column_widths[c - 1] + self.column_margins[c]
		for r in range(self.row_count):
			for c in range(self.column_count):
				if c <= len(self.rows[r]): # Don't try to set left on a cell which doesn't exist
					self.rows[r][c].rect.top = tops[r]
					self.rows[r][c].rect.left = lefts[c]
					if isinstance(self.rows[r][c], Layout):
						self.rows[r][c].position_rects()


	def widgets(self):
		"""
		A generator function which yields all the Widget instances contained in this Layout.
		"""
		for row in self.rows:
			for cell in row:
				if isinstance(cell, Layout):
					for e in cell.widgets():
						yield e
				else:
					yield cell


	def widget_at(self, pos):
		"""
		Returns the Widget at the given screen position (which is usually the mouse position).
		"""
		for row in self.rows:
			for cell in row:
				if cell.rect.collidepoint(pos):
					return cell if isinstance(cell, Widget) else cell.widget_at(pos)
		return None


	def dump(self, indent=0):
		"""
		Print this layout's element tree for debugging.
		"""
		print('  ' * indent + self.__str__())
		for row in self.rows:
			print('  ' * (indent + 1) + "row:")
			for cell in row:
				cell.dump(indent + 2)



class LinearLayout(Layout):

	"""
	Abstract base class of VerticalLayout and HorizontalLayout.
	Do not subclass this class. Use either VerticalLayout or HorizontalLayout.
	"""


	def __init__(self, *args):
		self.elements = []
		for arg in args:
			self.elements.append(arg)


	def append(self, arg):
		"""
		Add a Widget or Layout to this LinearLayout.
		Returns this LinearLayout.
		"""
		self.elements.append(arg)
		return self


	def position_rects(self):
		"""
		Set the final top, left position of contained elements.
		"""
		prev_elem = self.elements[0]
		prev_elem.rect.top = self.rect.top
		prev_elem.rect.left = self.rect.left
		for next_elem in self.elements[1:]:
			self.position_next_element(prev_elem, next_elem)
			prev_elem = next_elem
		for element in self.elements:
			if isinstance(element, Layout):
				element.position_rects()


	def widgets(self):
		"""
		A generator function which yields all the Widget instances contained in this Layout.
		"""
		for elem_a in self.elements:
			if isinstance(elem_a, Layout):
				for elem_b in elem_a.widgets():
					yield elem_b
			else:
				yield elem_a


	def widget_at(self, pos):
		"""
		Returns the Widget at the given screen position (which is usually the mouse position).
		"""
		for element in self.elements:
			if element.rect.collidepoint(pos):
				return element if isinstance(element, Widget) else element.widget_at(pos)
		return None


	def dump(self, indent=0):
		"""
		Print this layout's element tree for debugging.
		"""
		print('  ' * indent + self.__str__())
		for element in self.elements: element.dump(indent + 1)



class HorizontalLayout(LinearLayout):


	def get_initial_rect(self):
		"""
		Determine the minimum space necessary for this element and its' contained elements.
		Returns Rect
		"""
		if len(self.elements) == 0:
			raise Exception("Layout contains no elements")
		self.rect = Rect((0, 0), self.elements[0].get_initial_rect().size)
		prev_elem = self.elements[0]
		self.__internal_margins = 0
		for next_elem in self.elements[1:]:
			self.rect.height = max(self.rect.height, next_elem.get_initial_rect().height)
			margin = max(prev_elem.margin_right, next_elem.margin_left)
			self.rect.width += margin
			self.rect.width += next_elem.rect.width
			self.__internal_margins += margin
		return self.rect


	def justify_elements(self):
		"""
		Expand the area allowed to each element so that they fill available space.
		"""
		content_width = sum(element.rect.width for element in self.elements)
		target_content_width = self.rect.width - self.__internal_margins
		grow_factor = float(target_content_width) / float(content_width)
		for element in self.elements:
			element.rect.height = self.rect.height
			element.rect.width = round(element.rect.width * grow_factor)
			if isinstance(element, Layout): element.justify_elements()


	def position_next_element(self, prev_element, next_elem):
		"""
		Shift next_elem's rect by the width of prev_element's rect, plus margin.
		"""
		next_elem.rect.top = prev_element.rect.top
		next_elem.rect.left = prev_element.rect.left + prev_element.rect.width + \
			max(prev_element.margin_right, next_elem.margin_left)


	def __getattr__(self, varname):
		"""
		Retrieve margin values of this Layout from its contained elements.
		"""
		if varname == "margin_top":
			return max(elem.margin_top for elem in self.elements)
		elif varname == "margin_right":
			return self.elements[-1].margin_right
		elif varname == "margin_bottom":
			return max(elem.margin_bottom for elem in self.elements)
		elif varname == "margin_left":
			return self.elements[0].margin_left



class VerticalLayout(LinearLayout):


	def get_initial_rect(self):
		"""
		Determine the minimum space necessary for this element and its' contained elements.
		Returns Rect
		"""
		if len(self.elements) == 0:
			raise Exception("Layout contains no elements")
		self.rect = Rect((0, 0), self.elements[0].get_initial_rect().size)
		prev_elem = self.elements[0]
		self.__internal_margins = 0
		for next_elem in self.elements[1:]:
			self.rect.width = max(self.rect.width, next_elem.get_initial_rect().width)
			margin = max(prev_elem.margin_bottom, next_elem.margin_top)
			self.rect.height += margin
			self.rect.height += next_elem.rect.height
			self.__internal_margins += margin
		return self.rect


	def justify_elements(self):
		"""
		Expand the area allowed to each element so that they fill available space.
		"""
		content_height = sum(element.rect.height for element in self.elements)
		target_content_height = self.rect.height - self.__internal_margins
		grow_factor = float(target_content_height) / float(content_height)
		for element in self.elements:
			element.rect.width = self.rect.width
			element.rect.height = round(element.rect.height * grow_factor)
			if isinstance(element, Layout): element.justify_elements()


	def position_next_element(self, prev_element, next_elem):
		"""
		Shift next_elem's rect by the height of prev_element's rect, plus margin.
		"""
		next_elem.rect.top = prev_element.rect.top + prev_element.rect.height + \
			max(prev_element.margin_bottom, next_elem.margin_top)
		next_elem.rect.left = prev_element.rect.left


	def __getattr__(self, varname):
		"""
		Retrieve margin values of this Layout from its contained elements.
		"""
		if varname == "margin_top":
			return self.elements[0].margin_top
		elif varname == "margin_right":
			return max(elem.margin_right for elem in self.elements)
		elif varname == "margin_bottom":
			return self.elements[-1].margin_bottom
		elif varname == "margin_left":
			return max(elem.margin_left for elem in self.elements)




class Widget:

	rect						= None

	height						= None
	width						= None
	margin						= 10
	padding						= 8

	foreground_color			= (0, 0, 0)
	foreground_color_hover		= None
	foreground_color_focus		= None
	foreground_color_disabled	= None

	background_color			= (220, 220, 220)
	background_color_hover		= None
	background_color_focus		= None
	background_color_disabled	= None

	# Status bits:
	disabled					= False
	hovering					= False
	focused						= False
	dirty						= False	# Triggers repaint after appearance changes

	effect						= "no_effect"
	effect_func					= None
	bevel_depth					= 4
	border_radius				= 16


	def __init__(self, **kwargs):
		for varname, value in kwargs.items(): setattr(self, varname, value)
		# If no "effect" was passed in the kwargs, set the effect to the default for this class of Widget:
		if self.effect_func is None: self.effect_func = getattr(self, self.effect)


	def __setattr__(self, varname, value):
		"""
		Allows for setting margins or padding using tuples or single integers.
		----------------------------------------------------------------------
			Set all margins to 10px:
				widget.margin = 10
			Set top and bottom to 5px, left and right to 10px:
				widget.margin = (5, 10)
			Set each margin individually:
				widget.margin = (5, 10, 20, 10)
				order is (top, right, bottom, left)
		----------------------------------------------------------------------
		Allows for setting the rendering effect using a function name.
		Sets "dirty" on a Widget its visual appearance changes.
		"""
		if varname == "margin" and isinstance(value, tuple):
			if(len(value)) == 2:
				self.margin_top = value[0]		# Use "self.margin_x = value" to set "dirty"
				self.margin_bottom = value[0]
				self.margin_left = value[1]
				self.margin_right = value[1]
			elif(len(value)) == 4:
				self.margin_top = value[0]
				self.margin_right = value[1]
				self.margin_bottom = value[2]
				self.margin_left = value[3]
			else:
				raise Exception("Invalid margin value")
		elif varname == "padding" and isinstance(value, tuple):
			if(len(value)) == 2:
				self.padding_top = value[0]
				self.padding_bottom = value[0]
				self.padding_left = value[1]
				self.padding_right = value[1]
			elif(len(value)) == 4:
				self.padding_top = value[0]
				self.padding_right = value[1]
				self.padding_bottom = value[2]
				self.padding_left = value[3]
			else:
				raise Exception("Invalid padding value")
		elif varname == "effect":
			# Set the effect_func to the function identified by the string "effect":
			self.effect_func = getattr(self, value)
		elif varname == "enabled":
			varname = "disabled"
			value = not value
		# Set "dirty" only when a property changes:
		if varname != "dirty" and (varname not in self.__dict__ or self.__dict__[varname] != value):
			self.__dict__["dirty"] = True
		self.__dict__[varname] = value


	def __getattr__(self, varname):
		"""
		Returns value of "margin" if "margin_<side>" is not set. Same for padding.
		"""
		if varname == "margin_top" or varname == "margin_right" or \
			varname == "margin_bottom" or varname == "margin_left":
			return self.margin
		if varname == "padding_top" or varname == "padding_right" or \
			varname == "padding_bottom" or varname == "padding_left":
			return self.padding


	def current_foreground_color(self):
		"""
		Returns a color tuple; the foreground color appropriate for the current state
		(enabled, hovering, focused).
		If the color for that state is undefined, returns the default foreground color.
		"""
		if self.disabled:
			return self.foreground_color if self.foreground_color_disabled is None else self.foreground_color_disabled
		if self.focused:
			return self.foreground_color if self.foreground_color_focus is None else self.foreground_color_focus
		if self.hovering:
			return self.foreground_color if self.foreground_color_hover is None else self.foreground_color_hover
		return self.foreground_color


	def current_background_color(self):
		"""
		Returns a color tuple; the background color appropriate for the current state
		(enabled, hovering, focused).
		If the color for the current state is undefined, returns the default background color.
		"""
		if self.disabled:
			return self.background_color if self.background_color_disabled is None else self.background_color_disabled
		if self.focused:
			return self.background_color if self.background_color_focus is None else self.background_color_focus
		if self.hovering:
			return self.background_color if self.background_color_hover is None else self.background_color_hover
		return self.background_color


	def get_surface(self):
		"""
		Returns a Surface to use as this element's background, decorated with whichever effect function
		is set on this widget having been applied.
		"""
		surface = Surface(self.rect.size, SRCALPHA if self.effect == 'rounded_corners' else 0)
		return self.effect_func(surface)


	def no_effect(self, surface):
		"""
		A surface effect which returns a completely empty surface.
		"""
		return surface


	def solid_color(self, surface):
		"""
		Applies a solid color fill to this Widget's initial background surface.
		"""
		surface.fill(self.current_background_color())
		return surface


	def bevel(self, surface, inner=False):
		"""
		Applies a raised bevel effect to this Widget's initial background surface.
		"""
		color_tuple = self.current_background_color()
		surface.fill(color_tuple)
		color = Color(*color_tuple)
		highlight = color.correct_gamma(2) if inner else color.correct_gamma(0.75)
		shadow = color.correct_gamma(0.5) if inner else color.correct_gamma(1.5)
		bd = self.bevel_depth
		polygon(surface, highlight, [	# top
			(0,0),
			(self.rect.width, 0),
			(self.rect.width - bd, bd),
			(bd, bd)
		])
		polygon(surface, shadow, [		# right
			(self.rect.width, 0),
			(self.rect.width, self.rect.height),
			(self.rect.width - bd, self.rect.height - bd),
			(self.rect.width - bd, bd)
		])
		polygon(surface, shadow, [		# bottom
			(self.rect.width, self.rect.height),
			(0, self.rect.height),
			(bd, self.rect.height - bd),
			(self.rect.width - bd, self.rect.height - bd)
		])
		polygon(surface, highlight, [	# left
			(0,0),
			(bd, bd),
			(bd, self.rect.height - bd),
			(0, self.rect.height)
		])
		return surface


	def bevel_inset(self, surface):
		"""
		Applies an inset bevel effect to this Widget's initial background surface.
		"""
		return self.bevel(surface, True)


	def rounded_corners(self, surface):
		"""
		Applies a rounded corners effect to this Widget's initial background surface.
		"""
		bg = self.current_background_color()
		# points are (x, y)
		polygon(surface, bg, [
			(0, self.border_radius),
			(self.rect.width, self.border_radius),
			(self.rect.width, self.rect.height - self.border_radius),
			(0, self.rect.height - self.border_radius)
		])
		polygon(surface, bg, [
			(self.border_radius, 0),
			(self.rect.width - self.border_radius, 0),
			(self.rect.width - self.border_radius, self.rect.height),
			(self.border_radius, self.rect.height)
		])
		circle(surface, bg, (self.border_radius, self.border_radius), self.border_radius)
		circle(surface, bg, (self.rect.width - self.border_radius, self.border_radius), self.border_radius)
		circle(surface, bg, (self.rect.width - self.border_radius, self.rect.height - self.border_radius), self.border_radius)
		circle(surface, bg, (self.border_radius, self.rect.height - self.border_radius), self.border_radius)
		return surface


	def mouse_in(self):
		pass


	def mouse_out(self):
		pass


	def click(self, pos):
		pass


	def key_down(self, event):
		pass


	def __str__(self):
		return '%s "%s"  (%d x %d) @ (%d, %d)' % (
			self.__class__.__name__,
			self.text,
			self.rect.width, self.rect.height, self.rect.left, self.rect.top
		)


	def dump(self, indent=0):
		"""
		Print this widget's __str__(), formatted for debugging.
		"""
		print('  ' * indent + self.__str__())




class TextWidget(Widget):

	"""
	A Widget which displays text on its visible surface.
	"""

	foreground_color		= (0, 0, 0)
	align					= ALIGN_CENTER
	font					= 'FreeSans'
	font_size				= 16
	text					= ""

	text_rect				= None	# The area of the text surface, (top, left) relative to self.rect


	def __init__(self, text, **kwargs):
		self.text = text
		Widget.__init__(self, **kwargs)


	def get_initial_rect(self):
		"""
		Determine the minimum space necessary for this element and its' contained elements.
		Returns Rect
		"""
		self.font = pygame.font.SysFont(self.font, self.font_size)
		if self.height is None or self.width is None:
			w, h = self.font.size(self.text)
			if self.width is None:
				self.width = w
			if self.height is None:
				self.height = h
		self.rect = Rect(0, 0,
			self.padding_left + self.width + self.padding_right,
			self.padding_top + self.height + self.padding_bottom
		)
		return self.rect


	def get_surface(self):
		"""
		Returns a Surface with this TextWidget element's text rendered onto it.
		"""
		rendered_text = self.font.render(self.text, True, self.current_foreground_color())
		self.text_rect = rendered_text.get_rect()
		surface_rect = Rect((0, 0), self.rect.size)
		if self.align == ALIGN_CENTER:
			self.text_rect.center = surface_rect.center
		else:
			self.text_rect.centery = surface_rect.centery
			self.text_rect.left = self.padding_left if self.align == ALIGN_LEFT \
				else surface_rect.right - self.padding_right - self.text_rect.width
		surface = Widget.get_surface(self)
		surface.blit(rendered_text, self.text_rect)
		return surface



class Label(TextWidget):

	"""
	A Widget which displays text on its visible surface.
	"""

	effect						= "solid_color"



class Button(TextWidget):

	"""
	A Widget which displays text on its visible surface and may have a "click handler" attached.
	"""

	background_color			= (180, 180, 180)
	background_color_hover		= (180, 180, 50)
	background_color_focus		= (180, 180, 50)
	background_color_disabled	= (200, 200, 200)

	foreground_color_disabled	= (128, 128, 128)

	padding						= 16

	effect						= "bevel"
	click_handler				= None


	def click(self, pos):
		"""
		Click pseudo-event.
		"""
		if callable(self.click_handler): self.click_handler(self)



class Textbox(TextWidget):

	"""
	A Widget which renders a line cursor and accepts user input.
	"""

	background_color 			= (235, 235, 235)
	background_color_hover		= (245, 245, 245)
	background_color_focus		= (255, 255, 255)
	background_color_disabled	= (235, 235, 235)

	foreground_color			= (48, 48, 48)
	foreground_color_hover		= (48, 48, 48)
	foreground_color_focus		= (0, 0, 0)
	foreground_color_disabled	= (64, 64, 64)

	font_size					= 18

	cursor_color				= (120, 0, 0)
	effect						= "bevel_inset"
	bevel_depth					= 2

	cursor_position = 0

	__cursor_data = None
	__cursor_mask = None


	def __init__(self, text, **kwargs):
		TextWidget.__init__(self, text, **kwargs)
		if Textbox.__cursor_data is None:
			sel_text = (
				"XXXXXXXX        ",
				"  XXXX          ",
				"   XX           ",
				"   XX           ",
				"   XX           ",
				"   XX           ",
				"   XX           ",
				"   XX           ",
				"   XX           ",
				"   XX           ",
				"   XX           ",
				"   XX           ",
				"   XX           ",
				"   XX           ",
				"  XXXX          ",
				"XXXXXXXX        ")
			Textbox.__cursor_mask, Textbox.__cursor_data = pygame.cursors.compile(sel_text)


	def mouse_in(self):
		"""
		Sets the mouse cursor to a vertical bar to indicate that this is editable and
		to give the user an idea of where the cursor will be placed when this TextBox
		is clicked.
		"""
		pygame.mouse.set_cursor((16, 16), (3, 0), Textbox.__cursor_data, Textbox.__cursor_mask)


	def mouse_out(self):
		"""
		Restores the mouse cursor appearance to the default.
		"""
		pygame.mouse.set_cursor(*pygame.cursors.arrow)


	def key_down(self, event):
		"""
		Modify contained text and handle cursor movement keys.
		"""
		# Return "True" triggers a repaint
		if event.key == K_LEFT:					# left
			if self.cursor_position:
				if event.mod & KMOD_CTRL:		# ctrl-left
					self.cursor_position = self.previous_word_boundary(self.cursor_position)
				else:
					self.cursor_position -= 1
				return True
		elif event.key == K_RIGHT:				# right
			if self.cursor_position < len(self.text):
				if event.mod & KMOD_CTRL:		# ctrl-right
					self.cursor_position = self.next_word_boundary(self.cursor_position)
				else:
					self.cursor_position += 1
				return True
		elif event.key == K_BACKSPACE:			# backspace
			if self.cursor_position:
				if event.mod & KMOD_CTRL:		# ctrl-backspace
					cut_pos = self.previous_word_boundary(self.cursor_position)
				else:
					cut_pos = self.cursor_position - 1
				self.text = self.text[:cut_pos] + self.text[self.cursor_position:]
				self.cursor_position = cut_pos
				return True
		elif event.key == K_DELETE:				# delete
			if self.cursor_position < len(self.text):
				if event.mod & KMOD_CTRL:		# ctrl-delete
					cut_pos = self.next_word_boundary(self.cursor_position)
				else:
					cut_pos = self.cursor_position + 1
				self.text = self.text[:self.cursor_position] + self.text[cut_pos:]
				return True
		elif event.mod & KMOD_CTRL:
			return
		# --------------------- no ctrl key past here --------------------- #
		elif event.key == K_HOME:				# home
			if self.cursor_position:
				self.cursor_position = 0
				return True
		elif event.key == K_END:				# end
			if self.cursor_position < len(self.text):
				self.cursor_position = len(self.text)
				return True
		elif bool(event.unicode):
			self.text = self.text[:self.cursor_position] + \
				event.unicode + \
				self.text[self.cursor_position:]
			self.cursor_position += 1
			return True
		return False


	def previous_word_boundary(self, pos):
		"""
		Returns a cursor position (intger) marking the space previous to the given
		position.
		"""
		while pos and self.text[pos - 1].isspace(): pos -= 1
		word_boundary = self.text.rfind(' ', 0, pos)
		return 0 if word_boundary < 0 else word_boundary + 1


	def next_word_boundary(self, pos):
		"""
		Returns a cursor position (intger) marking the space following the given
		position.
		"""
		text_len = len(self.text);
		while pos < text_len and self.text[pos].isspace():
			pos += 1
		pos = self.text.find(' ', pos)
		return text_len if pos < 0 else pos


	def click(self, pos):
		"""
		Sets the cursor at the character position detected from the given (probably
		mouse) position.
		"""
		self.cursor_position = self.cursor_at(pos[0])


	def get_surface(self):
		"""
		Returns a Surface with this Textbox element's text and cursor indicator
		rendered onto it.
		"""
		surface = TextWidget.get_surface(self)	# Already includes text
		if self.focused:
			widget_x = self.cursor_indicator_widget_x(self.cursor_position)
			line(surface, self.cursor_color, (widget_x, self.text_rect.top), (widget_x, self.text_rect.bottom), 2)
		return surface


	def cursor_indicator_widget_x(self, cursor):
		"""
		Returns the x coordinate of the given cursor position, relative to self.rect.
		"""
		width, height = self.font.size(self.text[:cursor])
		return self.text_rect.left + width


	def cursor_at(self, abs_x):
		"""
		Determines the cursor position of the given absolute x coordinate.
		"""
		widget_x = abs_x - self.rect.left
		start = 0
		end = len(self.text)
		while start <= end:
			cursor = start + int((end - start) / 2)
			left = self.cursor_indicator_widget_x(cursor)
			if left > widget_x:
				end = cursor - 1
			elif left < widget_x:
				start = cursor + 1
			else:
				return cursor
		return cursor



class Radio(Widget):

	selected		= False
	value			= None				# (optional) value assigned to this Radio
	diameter		= 30				# Outside diameter of the radio circle
	dot_color		= (160, 160, 160)	# Color of the inner circle rendered when selected
	dot_radius		= 8					# Radius of the inner circle rendered when selected

	_groups			= {}				# Class variable; lists of radio widgets


	def __init__(self, group, text, **kwargs):
		"""
		Initialize a Radio Widget.
		.
		"group" identifies the group that this Radio is a member of. Only one Radio in
		a group may be selected at a time.

		"text" is the text to show on the associated label.
		"""
		self.group = group
		if group not in Radio._groups: Radio._groups[group] = []
		Radio._groups[group].append(self)
		Widget.__init__(self, **kwargs)
		self._label = Label(text, **kwargs)


	@classmethod
	def selected_element(cls, group):
		"""
		Returns the selected Radio instance having the given "group" id.
		Returns none if no Radio in the given group is selected.
		"""
		if group in Radio._groups:
			for radio in Radio._groups[group]:
				if radio.selected: return radio
		return None


	@classmethod
	def selected_value(cls, group):
		"""
		Returns the "value" attribute of the selected Radio instance having the given "group" id.
		If the Radio widget's value is "None", returns the "text" attribute of the Radio's label.
		Returns none if no Radio in the given group is selected.
		"""
		radio = Radio.selected_element(group)
		if radio is None: return None
		return radio.text if radio.value is None else radio.value


	def __setattr__(self, varname, value):
		"""
		Delegate the "text" attribute to the label contained in this Radio widget.
		"""
		if varname == "text":
			self._label.text = value
		else:
			super(Radio, self).__setattr__(varname, value)


	def __getattr__(self, varname):
		"""
		Delegate the "text" attribute to the label contained in this Radio widget.
		"""
		if varname == "text":
			return self._label.text
		if varname == "value" and self.__dict__["value"] is None:
			return self._label.text
		return super(Radio, self).__getattr__(varname)


	def get_initial_rect(self):
		"""
		Determine the minimum space necessary for this element and its' contained elements.
		Returns Rect
		"""
		self._circle_rect = Rect(0, 0, self.diameter, self.diameter)
		self._circle_boundary = self._circle_rect.inflate(self.padding_left, self.padding_top + self.padding_bottom)
		self._circle_boundary.topleft = 0, 0
		self._label_rect = self._label.get_initial_rect()
		self._label_rect.left = self._circle_boundary.width
		self.rect = self._circle_boundary.union(self._label_rect)
		self._label_rect.centery = self.rect.centery
		self._circle_boundary.centery = self.rect.centery
		self._circle_rect.center = self._circle_boundary.center
		return self.rect


	def get_surface(self):
		"""
		Returns a Surface to use as this element's background, decorated with whichever effect function
		is set on this widget having been applied.
		"""
		surface = Surface(self.rect.size)
		surface.fill(self.current_background_color())

		color = Color(*self.current_background_color())
		highlight = color.correct_gamma(2)
		shadow = color.correct_gamma(0.5)
		arc(surface, shadow, self._circle_rect, RADIANS_TOPRIGHT, RADIANS_BOTTOM_LEFT, self.bevel_depth)
		arc(surface, highlight, self._circle_rect, RADIANS_BOTTOM_LEFT, RADIANS_TOPRIGHT, self.bevel_depth)

		if self.selected:
			circle(surface, self.dot_color, self._circle_rect.center, self.dot_radius)

		for att in ["disabled", "focused", "hovering"]:
			setattr(self._label, att, getattr(self, att))
		surface.blit(self._label.get_surface(), self._label_rect.topleft)
		return surface


	def click(self, pos):
		"""
		Click pseudo-event.
		"""
		for radio in Radio._groups[self.group]: radio.selected = False
		self.selected = True
		if callable(self.click_handler): self.click_handler(self)


	def __str__(self):
		return 'Radio ["%s" group] "%s" (%d x %d) @ (%d, %d)' % (
			self.group, self.text,
			self.rect.width, self.rect.height, self.rect.left, self.rect.top
		)





class Dialog(VerticalLayout):

	caption				= ""
	background_color	= (220, 220, 220)


	def __init__(self, *args):
		"""
		Pass an optional list of layouts or widgets to initially append to the dialog.
		"""
		pygame.font.init()
		VerticalLayout.__init__(self, *args)
		self._run_loop = True
		self.__hovered_widget = None
		self.__focused_widget = None


	def set_caption(self, caption):
		"""
		Sets the window caption.
		"""
		self.caption = caption
		return self


	def get_initial_rect(self):
		"""
		Determine the minimum space necessary for this element and its' contained elements.
		Returns Rect
		"""
		VerticalLayout.get_initial_rect(self)
		self.rect.left = self.margin_left
		self.rect.top = self.margin_top
		return self.rect


	def show(self):
		"""
		Initialize the display and enter the event loop.
		The display is destroyed when this function exits.
		"""
		self.initialize_display()
		self._main_loop()
		display.quit()


	def initialize_display(self):
		"""
		Initialize the pygame display and do initial render.
		"""
		display.init()
		self.rect = self.get_initial_rect()
		self.screen_rect = Rect((0, 0,
			self.rect.width + self.margin_left + self.margin_right,
			self.rect.height + self.margin_top + self.margin_bottom
		))
		os.environ['SDL_VIDEO_CENTERED'] = '1'
		self.screen = display.set_mode(self.screen_rect.size)
		self.screen.fill(self.background_color)
		display.set_caption(self.caption)
		self.justify_elements()
		self.position_rects()
		for widget in self.widgets():
			self.screen.blit(widget.get_surface(), widget.rect)
		display.update()


	def _main_loop(self):
		"""
		pygame event loop - respond to pygame events and call handlers for those events.
		"""
		self.mouse_down_widget = None
		event_handlers = {
			ACTIVEEVENT:		self._noop,				# 1
			KEYDOWN:			self._keydown,			# 2
			KEYUP:				self._noop,				# 3
			MOUSEMOTION:		self._mousemotion,		# 4
			MOUSEBUTTONDOWN:	self._mousebuttondown,	# 5
			MOUSEBUTTONUP:		self._mousebuttonup,	# 6
			JOYAXISMOTION:		self._noop,				# 7
			JOYBALLMOTION:		self._noop,				# 8
			JOYHATMOTION:		self._noop,				# 9
			JOYBUTTONDOWN:		self._noop,				# 10
			JOYBUTTONUP:		self._noop,				# 11
			QUIT:				self._quit,				# 12
			VIDEORESIZE:		self._noop,				# 16
			VIDEOEXPOSE:		self._noop,				# 17
		}
		while self._run_loop:
			self.loop_start()
			for event in pygame.event.get(): event_handlers[event.type](event)
			self.loop_end()
			dirty_rects = []
			for widget in self.widgets():
				if widget.dirty:
					self.screen.fill(self.background_color, widget.rect)
					self.screen.blit(widget.get_surface(), widget.rect)
					dirty_rects.append(widget.rect)
					widget.dirty = False
			if len(dirty_rects): display.update(dirty_rects)
		for cls in self.__class__.mro():
			if "exit_loop" in cls.__dict__:
				cls.exit_loop(self)


	def loop_start(self):
		"""
		Called at the beginning of _main_loop() each time through, before processing events.
		The event loop looks like this:
		1. loop_start()                              <-- you are here
		2. event handling (keyboard, mouse, timers)
		3. loop_end()
		4. repaint the dialog
		5. update the display

		This function does nothing, and is meant for being overriden by a subclass.
		"""
		pass


	def loop_end(self):
		"""
		Called at the end of _main_loop() each time through.
		The event loop looks like this:
		1. loop_start()
		2. event handling (keyboard, mouse, timers)
		3. loop_end()                                <-- you are here
		4. repaint the dialog
		5. update the display

		This function does nothing, and is meant for being overriden by a subclass.
		"""
		pass


	def _keydown(self, event):
		"""
		Handle KEYDOWN event - called from _main_loop.
		"""
		if event.mod & KMOD_ALT:
			pass
		elif event.key == K_ESCAPE:
			self._quit(event)
		elif (event.key == K_RETURN or event.key == K_SPACE) and self.__focused_widget is not None:
			self.__focused_widget.click(NO_POSITION)
		elif event.key == K_TAB:
			if self.__focused_widget is None:
				self.__focused_widget = self.last_focusable_widget() \
					if event.mod & KMOD_SHIFT \
					else self.first_focusable_widget()
			else:
				neighbor = self.focusable_widget_before(self.__focused_widget) \
					if event.mod & KMOD_SHIFT \
					else self.focusable_widget_after(self.__focused_widget)
				if neighbor is None:
					neighbor = self.last_focusable_widget() \
						if event.mod & KMOD_SHIFT \
						else self.first_focusable_widget()
				self.__focused_widget.focused = False
				self.__focused_widget = neighbor
			self.__focused_widget.focused = True
		elif self.__focused_widget is not None and not self.__focused_widget.disabled:
			self.__focused_widget.key_down(event)


	def _mousemotion(self, event):
		"""
		Handle MOUSEMOTION event - called from _main_loop.
		"""
		widget = self.widget_at(event.pos)
		if widget is not self.__hovered_widget:
			if isinstance(self.__hovered_widget, Widget):
				self.__hovered_widget.hovering = False
				self.__hovered_widget.mouse_out()
			if widget is not None:
				widget.hovering = True
				widget.mouse_in()
		self.__hovered_widget = widget


	def _mousebuttondown(self, event):
		"""
		Handle MOUSEBUTTONDOWN event - called from _main_loop.
		"""
		self.mouse_down_widget = self.widget_at(event.pos)
		if self.__focused_widget is not None and self.__focused_widget is not self.mouse_down_widget:
			self.__focused_widget.focused = False


	def _mousebuttonup(self, event):
		"""
		Handle MOUSEBUTTONUP event - called from _main_loop.
		"""
		widget = self.widget_at(event.pos)
		if widget is not None and widget is self.mouse_down_widget and not widget.disabled:
			widget.focused = True
			widget.click(event.pos)
			self.__focused_widget = widget


	def _quit(self, event):
		"""
		Handle QUIT event or K_ESCAPE key pressed - called from _main_loop.
		"""
		self.close()


	def _noop(self, event):
		"""
		Consumes events not needing to be handled by this dialog.
		"""
		pass


	def close(self):
		"""
		Flags to exit the main loop. (thread safe). The _main_loop function will fall
		through to "exit_loop()" after this is called.
		"""
		self._run_loop = False


	def dump(self, indent=0):
		"""
		Print this layout's element tree for debugging.
		"""
		if self.rect is None:
			self.get_initial_rect()
			self.justify_elements()
			self.position_rects()
		super(Dialog, self).dump(indent)





if __name__ == '__main__':
	import sys, time, argparse

	p = argparse.ArgumentParser()
	p.add_argument("--dump", "-d", action="store_true", help="Dump description of dialog structure")
	p.add_argument("--grid", "-g", action="store_true", help="Show test dialog with grid layout")
	p.add_argument("--roundies", "-r", action="store_true", help="Decorate widgets with rounded corners")
	options = p.parse_args()

	pygame.font.init()

	def click_handler(elem):
		print(elem.__str__())
		if isinstance(elem, Radio):
			print("Selected: %s" % Radio.selected_element(elem.group))
			print("Value: %s" % Radio.selected_value(elem.group))

	status_label = Label("Status label", font_size=22)

	if options.grid:
		grid = GridLayout(
			[Label("First textbox:", align=ALIGN_RIGHT), Textbox("This is a textbox"), Textbox("This is a textbox")],
			[Label("Second textbox:", align=ALIGN_RIGHT), Textbox("This is a textbox"), Textbox("This is a textbox")],
			[Label("Third textbox:", align=ALIGN_RIGHT), Textbox("This is a textbox"), Textbox("This is a textbox")],
			[Label("Fourth textbox:", align=ALIGN_RIGHT), Textbox("This is a textbox"), Textbox("This is a textbox")],
			[Label("Fifth textbox:", align=ALIGN_RIGHT), Textbox("This is a textbox"), Textbox("This is a textbox")]
		)
		for widget in grid.widgets(): widget.margin = 0
		dialog = Dialog(
			HorizontalLayout(
				grid,
				VerticalLayout(
					Button("Button One", click_handler=click_handler),
					Button("Button Two (disabled)", disabled=True, click_handler=click_handler),
					Button("Button Three", click_handler=click_handler)
				)
			),
			Button("Bottom button", click_handler=click_handler),
			status_label
		)

	else:
		dialog = Dialog(
			Textbox("Input one and a two", align=ALIGN_CENTER, width=360),
			Button("Bottom Button", padding=22, click_handler=click_handler),
			HorizontalLayout(
				Radio("group1", "Option 1", align=ALIGN_RIGHT, click_handler=click_handler),
				Radio("group1", "Option 2", value="SET_VALUE", align=ALIGN_LEFT, click_handler=click_handler)
			),
			status_label
		)

	if options.roundies:
		for widget in dialog.widgets():
			if widget.__class__.__name__ == "Textbox" or widget.__class__.__name__ == "Button":
				widget.effect = "rounded_corners"

	if options.dump:

		print("\nIntial rects:")
		dialog.get_initial_rect()
		dialog.dump()
		print

		dialog.justify_elements()
		print("\nAfter growing rects to fit available space:")
		dialog.dump()
		print

		dialog.position_rects()
		print("\nAfter positioning:")
		dialog.dump()

	else:
		dialog.caption = "Dialog test"
		dialog.show()

	sys.exit(0)



