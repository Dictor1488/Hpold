package inq.hpold.battle
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.Shape;
   import flash.display.Sprite;
   import flash.events.Event;
   import flash.filters.DropShadowFilter;
   import flash.text.TextField;
   import flash.text.TextFormat;
   import flash.utils.Dictionary;
   import inq.hpold.injector.BattleDisplayable;

   /**
    * Independent HP bars. No OldSkool SWF, HTML images or bitmap scaling.
    * One row per vehicle: painted background, HP fill and centered label.
    */
   public class PlayerPanelsUI extends BattleDisplayable
   {
      private static const WIDTH:Number = 84;
      private static const HEIGHT:Number = 16;
      private var _rows:Dictionary = new Dictionary();

      public function PlayerPanelsUI()
      {
         super();
         addEventListener(Event.ENTER_FRAME, relayout);
      }

      public function as_create(linkage:String, kind:String, config:Object):void
      {
         // Retained for the DAAPI contract; rows are created by as_update.
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
         row.visible = Boolean(data.visible) && Number(data.maximum) > 0 &&
                       Number(data.current) > 0;
         var current:int = Math.max(0, int(data.current));
         var maximum:int = Math.max(1, int(data.maximum));
         var ratio:Number = Math.max(0, Math.min(1, Number(current) / maximum));
         var fill:Shape = row.getChildByName("fill") as Shape;
         var label:TextField = row.getChildByName("hpLabel") as TextField;
         var enemy:Boolean = placeRow(id, row);
         fill.graphics.clear();
         if (Boolean(data.showBar))
         {
            fill.graphics.beginFill(enemy ? 0xCF3934 : 0x6DBB38);
            fill.graphics.drawRoundRect(1, 1, (WIDTH - 2) * ratio, HEIGHT - 2, 3, 3);
            fill.graphics.endFill();
         }
         label.text = current + "/" + maximum;
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
         }
      }

      private function makeRow():Sprite
      {
         var row:Sprite = new Sprite();
         row.mouseEnabled = false;
         row.mouseChildren = false;
         var background:Shape = new Shape();
         background.graphics.beginFill(0x111A19, 0.92);
         background.graphics.drawRoundRect(0, 0, WIDTH, HEIGHT, 4, 4);
         background.graphics.endFill();
         background.graphics.lineStyle(1, 0x000000, 0.65);
         background.graphics.drawRoundRect(0.5, 0.5, WIDTH - 1, HEIGHT - 1, 4, 4);
         row.addChild(background);
         var fill:Shape = new Shape();
         fill.name = "fill";
         row.addChild(fill);
         var label:TextField = new TextField();
         label.name = "hpLabel";
         label.defaultTextFormat = new TextFormat("Arial", 11, 0xFFFFFF, true, null, null, null, null, "center");
         label.width = WIDTH;
         label.height = 20;
         label.x = 0;
         label.y = -2;
         label.selectable = false;
         label.mouseEnabled = false;
         label.wordWrap = false;
         label.filters = [new DropShadowFilter(1, 90, 0, 1, 2, 2, 2)];
         row.addChild(label);
         return row;
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
            row.y = Math.round(icon.y + 2);
            return enemy;
         }
         catch (e:Error)
         {
            trace("[inq_hpold] placeRow " + vehicleID + ": " + e.message);
            return false;
         }
      }

      private function relayout(event:Event):void
      {
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
