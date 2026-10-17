package inq.hpold.battle
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.events.Event;
   import flash.text.TextField;
   import flash.text.TextFieldAutoSize;
   import flash.text.TextFormat;
   import flash.filters.DropShadowFilter;
   import flash.utils.Dictionary;
   import flash.utils.getTimer;
   import inq.hpold.injector.BattleDisplayable;

   // Standalone reconstruction of OldSkool PlayerPanelsUI.
   // Fields belong to vehicle-list items, not a separate panel overlay.
   public class PlayerPanelsUI extends BattleDisplayable
   {
      private var _configs:Object = {};
      private var _fields:Object = {};
      private var _lastLayout:int = 0;

      public function PlayerPanelsUI()
      {
         super();
         name = "PlayerPanelsUI";
         addEventListener(Event.ENTER_FRAME, onFrame);
      }

      public function as_create(linkage:String, kind:String, config:Object):void
      {
         if (kind != "Label" || !linkage || config == null)
            return;
         _configs[linkage] = config;
         if (_fields[linkage] == null)
            _fields[linkage] = new Dictionary();
      }

      public function as_update(linkage:String, data:Object):void
      {
         if (data == null || _configs[linkage] == null || !data.hasOwnProperty("vehicleID"))
            return;
         var vehicleID:int = int(data.vehicleID);
         var record:Object = getField(linkage, vehicleID);
         record.text = data.hasOwnProperty("text") ? String(data.text) : "";
         attachAndDraw(linkage, vehicleID, record);
      }

      public function as_delete(linkage:String):void
      {
         var items:Dictionary = _fields[linkage] as Dictionary;
         if (items != null)
         {
            for each (var record:Object in items)
            {
               var field:TextField = record.field as TextField;
               if (field != null && field.parent != null)
                  field.parent.removeChild(field);
            }
         }
         delete _fields[linkage];
         delete _configs[linkage];
      }

      private function getField(linkage:String, vehicleID:int):Object
      {
         var items:Dictionary = _fields[linkage] as Dictionary;
         var record:Object = items[vehicleID];
         if (record != null)
            return record;

         var field:TextField = new TextField();
         field.name = linkage + "_" + vehicleID;
         field.mouseEnabled = false;
         field.selectable = false;
         field.multiline = false;
         field.wordWrap = false;
         field.embedFonts = false;
         field.autoSize = TextFieldAutoSize.NONE;
         record = {field: field, text: "", renderedText: null, renderedSide: null};
         items[vehicleID] = record;
         return record;
      }

      private function getMember(target:*, key:String):*
      {
         if (target == null)
            return null;
         try { return target[key]; } catch (e:Error) {}
         return null;
      }

      private function findVehicle(vehicleID:int):Object
      {
         var panel:* = getMember(battlePage, "playersPanel");
         if (panel == null)
            panel = getMember(battlePage, "epicRandomPlayersPanel");
         if (panel == null)
            return null;
         for each (var side:String in ["left", "right"])
         {
            var list:* = getMember(panel, side == "left" ? "listLeft" : "listRight");
            if (list == null)
               continue;
            var holder:*;
            try { holder = list.getHolderByVehicleID(vehicleID); }
            catch (e:Error)
            {
               try { holder = list.getHolderByVehicleId(vehicleID); }
               catch (e2:Error) {}
            }
            if (holder == null)
               continue;
            var item:*;
            try { item = holder.getListItem(); } catch (e3:Error) {}
            if (item == null)
               item = getMember(holder, "_listItem");
            if (item == null)
               item = getMember(holder, "listItem");
            if (item is DisplayObjectContainer)
               return {item: item, side: side};
         }
         return null;
      }

      private function attachAndDraw(linkage:String, vehicleID:int, record:Object):void
      {
         var location:Object = findVehicle(vehicleID);
         var field:TextField = record.field as TextField;
         if (location == null)
         {
            field.visible = false;
            return;
         }
         var item:DisplayObjectContainer = location.item as DisplayObjectContainer;
         if (field.parent != item)
         {
            if (field.parent != null)
               field.parent.removeChild(field);
            item.addChild(field);
         }
         var config:Object = _configs[linkage];
         var side:Object = config[location.side];
         if (side == null)
            return;
         var icon:DisplayObject = getMember(item, "vehicleIcon") as DisplayObject;
         var vehicleTF:DisplayObject = getMember(item, "vehicleTF") as DisplayObject;
         var anchor:DisplayObject = icon != null ? icon : vehicleTF;
         // OldSkool API offsets are relative to the vehicle icon's position.
         field.x = Math.round((anchor != null ? anchor.x : 0) + Number(side.x || 0));
         field.y = Math.round((anchor != null ? anchor.y : 0) + Number(side.y || 0));
         field.width = side.hasOwnProperty("width") ? Number(side.width) : 100;
         field.height = side.hasOwnProperty("height") ? Number(side.height) : 24;
         if (record.renderedText !== record.text || record.renderedSide !== location.side)
         {
            var format:TextFormat = new TextFormat("$FieldFont", 11, 0xFFFFFF);
            format.align = side.hasOwnProperty("align") ? String(side.align) : location.side;
            field.defaultTextFormat = format;
            field.filters = [new DropShadowFilter(0, 0, 0x000000, 0.9, 2, 2, 2, 1)];
            if (config.isHtml)
               field.htmlText = record.text;
            else
               field.text = record.text;
            // Do not call setTextFormat after setting htmlText: it rewrites
            // formatting of the HTML field on every layout sync.
            record.renderedText = record.text;
            record.renderedSide = location.side;
         }
         field.visible = item.visible && record.text != "";
      }

      private function onFrame(e:Event):void
      {
         var now:int = getTimer();
         if (now - _lastLayout < 250)
            return;
         _lastLayout = now;
         for (var linkage:String in _fields)
         {
            var items:Dictionary = _fields[linkage] as Dictionary;
            for (var vehicle:* in items)
               attachAndDraw(linkage, int(vehicle), items[vehicle]);
         }
      }

      override protected function onDispose():void
      {
         removeEventListener(Event.ENTER_FRAME, onFrame);
         for (var linkage:String in _fields)
            as_delete(linkage);
         super.onDispose();
      }
   }
}
