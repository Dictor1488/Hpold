package inq.hpold.battle
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.Sprite;
   import flash.events.Event;
   import flash.text.TextField;
   import flash.utils.Dictionary;
   import flash.utils.getTimer;
   import inq.hpold.injector.BattleDisplayable;

   /**
    * Standalone renderer matching PlayersPanelHP 1.2.4 and its
    * playersPanelAPI_modsCore.swf TextField implementation.
    */
   public class PlayerPanelsUI extends BattleDisplayable
   {
      private static const BAR_WIDTH:Number = 72;
      private static const BAR_HEIGHT:Number = 14;
      private static const FIELD_HEIGHT:Number = 24;
      private static const LABEL_WIDTH:Number = 100;

      private var _rows:Dictionary = new Dictionary();
      private var _wanted:Dictionary = new Dictionary();
      private var _fillWidths:Dictionary = new Dictionary();
      private var _showBars:Dictionary = new Dictionary();
      private var _lastLayout:int = 0;

      public function PlayerPanelsUI()
      {
         super();
         addEventListener(Event.ENTER_FRAME, relayout);
      }

      public function as_create(linkage:String, kind:String, config:Object):void
      {
         // Rows are created lazily by as_update.
      }

      public function as_update(linkage:String, data:Object):void
      {
         if (linkage != "hp_row" || data == null || !data.hasOwnProperty("vehicleID"))
            return;

         var id:int = int(data.vehicleID);
         var row:Sprite = _rows[id] as Sprite;
         if (row == null)
         {
            row = makeRow();
            _rows[id] = row;
         }

         var current:int = Math.max(0, int(data.current));
         var maximum:int = Math.max(1, int(data.maximum));
         var ratio:Number = Math.max(0, Math.min(1, Number(current) / maximum));
         _fillWidths[id] = Math.ceil(BAR_WIDTH * ratio);
         _showBars[id] = Boolean(data.showBar);
         _wanted[id] = Boolean(data.visible) && Number(data.maximum) > 0 && current > 0;

         var label:TextField = row.getChildByName("hpLabel") as TextField;
         label.htmlText = "<font face='$FieldFont' color='#FFFFFF' size='11'>" +
                          current + "/" + maximum + "</font>";

         var enemy:Boolean = placeRow(id, row);
         updateFill(row, enemy, int(_fillWidths[id]), Boolean(_showBars[id]));
         row.visible = Boolean(_wanted[id]);
      }

      public function as_delete(linkage:String):void
      {
         if (linkage != "hp_row")
            return;
         for (var id:* in _rows)
         {
            var row:Sprite = _rows[id] as Sprite;
            if (row && row.parent)
               row.parent.removeChild(row);
            delete _rows[id];
            delete _wanted[id];
            delete _fillWidths[id];
            delete _showBars[id];
         }
      }

      private function makeRow():Sprite
      {
         var row:Sprite = new Sprite();
         row.mouseEnabled = false;
         row.mouseChildren = false;

         // Original 3bg Label: default 100x24 field at bar position + (1, 1).
         var background:TextField = makeField("background", LABEL_WIDTH, FIELD_HEIGHT);
         background.x = 1;
         background.y = 1;
         background.htmlText = "<img src='img://gui/hpbars/hp_bg.png' width='68' height='12'>";
         row.addChild(background);

         // Original 2img Label: 72x24 field; image width is updated with ceil().
         var fill:TextField = makeField("fill", BAR_WIDTH, FIELD_HEIGHT);
         row.addChild(fill);

         // Original 1text Label: default 100x24 field and HTML $FieldFont.
         var label:TextField = makeField("hpLabel", LABEL_WIDTH, FIELD_HEIGHT);
         row.addChild(label);
         return row;
      }

      private function makeField(name:String, width:Number, height:Number):TextField
      {
         var field:TextField = new TextField();
         field.name = name;
         field.visible = true;
         field.width = width;
         field.height = height;
         field.selectable = false;
         field.mouseEnabled = false;
         return field;
      }

      private function updateFill(row:Sprite, enemy:Boolean, width:int, showBar:Boolean):void
      {
         var fill:TextField = row.getChildByName("fill") as TextField;
         fill.visible = showBar && width > 0;
         if (!fill.visible)
         {
            fill.htmlText = "";
            return;
         }

         var asset:String = "hp_alive_l.png";
         if (enemy)
            asset = isColorBlindMode() ? "hp_alive_cb.png" : "hp_alive_r.png";
         fill.htmlText = "<img src='img://gui/hpbars/" + asset +
                         "' width='" + width + "' height='" + BAR_HEIGHT + "'>";
      }

      private function isColorBlindMode():Boolean
      {
         try
         {
            return App != null && App.colorSchemeMgr != null &&
                   Boolean(App.colorSchemeMgr.getIsColorBlindS());
         }
         catch (e:Error)
         {
            return false;
         }
         return false;
      }

      private function placeRow(vehicleID:int, row:Sprite):Boolean
      {
         try
         {
            if (battlePage == null)
               return false;
            var panel:* = battlePage["playersPanel"];
            if (panel == null)
               return false;
            var holder:* = panel.listLeft.getHolderByVehicleID(vehicleID);
            var enemy:Boolean = false;
            if (holder == null)
            {
               holder = panel.listRight.getHolderByVehicleID(vehicleID);
               enemy = true;
            }
            if (holder == null || holder._listItem == null)
            {
               row.visible = false;
               return enemy;
            }

            var item:DisplayObjectContainer = holder._listItem as DisplayObjectContainer;
            if (item == null || holder._listItem.vehicleIcon == null)
               return enemy;
            if (row.parent != item)
            {
               if (row.parent != null)
                  row.parent.removeChild(row);
               item.addChild(row);
            }

            var icon:DisplayObject = holder._listItem.vehicleIcon as DisplayObject;
            row.x = Math.round(icon.x + (enemy ? -176 : 85));
            row.y = Math.round(icon.y + 3);

            // Original text field x values are -160/100 while bar values are
            // -176/85, hence offsets 16 and 15 inside this row.
            var label:TextField = row.getChildByName("hpLabel") as TextField;
            label.x = enemy ? 16 : 15;
            label.y = 0;

            updateFill(row, enemy, int(_fillWidths[vehicleID]), Boolean(_showBars[vehicleID]));
            row.visible = Boolean(_wanted[vehicleID]);
            return enemy;
         }
         catch (e:Error)
         {
            trace("[inq_hpold] placeRow " + vehicleID + ": " + e.message);
            return false;
         }
         // Flex 4.16's older control-flow analyzer requires a final return.
         return false;
      }

      private function relayout(event:Event):void
      {
         var now:int = getTimer();
         if (now - _lastLayout < 250)
            return;
         _lastLayout = now;
         for (var id:* in _rows)
         {
            var row:Sprite = _rows[id] as Sprite;
            if (row != null)
               placeRow(int(id), row);
         }
      }

      override protected function onDispose():void
      {
         removeEventListener(Event.ENTER_FRAME, relayout);
         as_delete("hp_row");
         super.onDispose();
      }
   }
}
